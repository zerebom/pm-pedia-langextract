"""Integration extractor for project unification."""

import langextract as lx
from pathlib import Path
import textwrap
import json
from typing import List, Dict, Any
from datetime import datetime

from pm_pedia_langextract.poc.few_shot_examples import get_integration_examples
from pm_pedia_langextract.utils.logging_config import get_logger

logger = get_logger(__name__)


class IntegrationExtractor:
    """スニペット群から統合データを生成する."""
    
    def __init__(self, model_id: str = "gemini-2.5-flash-lite"):
        self.model_id = model_id
        self.prompt = textwrap.dedent("""
            複数のドキュメントから抽出されたスニペット群を分析し、
            プロジェクト単位で情報を統合・構造化してください。
            
            タスク:
            1. 同一プロジェクトを指す異なる表現を名寄せ
            2. プロジェクトごとに情報を集約
            3. 現在のステータスを推定
            4. 包括的なサマリーを生成
            
            抽出ルール:
            - 「スマートタグ」「スマートタグ機能」「タグクラスタリング」は同一プロジェクト
            - 「マルチデータソース」「マルチデータソース対応」は同一プロジェクト
            - 各プロジェクトに一意のproject_id (proj_001, proj_002...)を付与
            - ステータスは「順調」「停滞」「要確認」「完了」「不明」から選択
            
            出力属性:
            - project_id: 一意のID
            - project_name: 統一されたプロジェクト名
            - aliases: 名寄せした別名のリスト
            - status: 現在の状態
            - summary: プロジェクトの現状説明
            - key_themes: 主要なテーマやキーワード
            - people: 関連する人物
            
            重要: 必ずproject単位で情報を統合し、複数のprojectを抽出してください。
        """)
        self.examples = get_integration_examples()
    
    def load_snippets(self, snippet_files: List[Path]) -> str:
        """複数のスニペットファイルを読み込んで統合."""
        logger.info(f"スニペットファイル読み込み開始: {len(snippet_files)}件")
        
        all_snippets = []
        
        for file_path in snippet_files:
            logger.debug(f"読み込み中: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            data = json.loads(line)
                            doc_name = file_path.stem.replace('_snippets', '')
                            
                            for extraction in data.get('extractions', []):
                                snippet_info = {
                                    'document': doc_name,
                                    'type': extraction.get('extraction_class'),
                                    'content': extraction.get('extraction_text'),
                                    'attributes': extraction.get('attributes', {})
                                }
                                all_snippets.append(snippet_info)
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON解析エラー {file_path}:{line_num}: {e}")
                            continue
                            
            except Exception as e:
                logger.error(f"ファイル読み込みエラー {file_path}: {e}")
                continue
        
        logger.info(f"総スニペット数: {len(all_snippets)}件")
        
        # テキスト形式に変換
        text_output = "抽出されたスニペット一覧:\n\n"
        current_doc = None
        snippet_count = 0
        
        for snippet in all_snippets:
            if snippet['document'] != current_doc:
                current_doc = snippet['document']
                text_output += f"\n[Document: {current_doc}]\n"
            
            text_output += f"- {snippet['type']}: \"{snippet['content']}\"\n"
            
            # プロジェクトキーワードを表示
            project_keywords = snippet['attributes'].get('project_keywords', [])
            if project_keywords:
                text_output += f"  Keywords: {', '.join(project_keywords)}\n"
            
            # 関係者を表示
            people = snippet['attributes'].get('people', [])
            if people:
                text_output += f"  People: {', '.join(people)}\n"
                
            snippet_count += 1
            
            # 長すぎる場合は制限
            if snippet_count >= 50:
                text_output += f"\n... (残り{len(all_snippets) - snippet_count}件は省略) ...\n"
                break
        
        logger.debug(f"統合テキスト長: {len(text_output)}文字")
        return text_output
    
    def extract(self, snippet_files: List[Path]) -> Dict[str, Any]:
        """スニペットファイルから統合データを生成."""
        logger.info("=== Phase 2: 統合・構造化処理開始 ===")
        
        # スニペットを統合テキストに変換
        logger.info("ステップ1: スニペット統合テキスト生成")
        integrated_text = self.load_snippets(snippet_files)
        
        # LangExtractで統合処理
        logger.info("ステップ2: LLMによる統合処理実行")
        try:
            result = lx.extract(
                text_or_documents=integrated_text,
                prompt_description=self.prompt,
                examples=self.examples,
                model_id=self.model_id,
                extraction_passes=1,
                max_workers=1
            )
            
            logger.info(f"統合処理完了: {len(result.extractions)}件の抽出")
            
        except Exception as e:
            logger.error("LLM統合処理でエラー", exc_info=True)
            raise
        
        # 結果を構造化
        logger.info("ステップ3: 結果の構造化")
        projects = []
        for extraction in result.extractions:
            if extraction.extraction_class == "project":
                attrs = extraction.attributes or {}
                
                # 関連スニペットを収集（簡易版）
                related_snippets = self._collect_related_snippets(
                    extraction.extraction_text, 
                    attrs.get("aliases", []),
                    snippet_files
                )
                
                project = {
                    "project_id": attrs.get("project_id", f"proj_{len(projects)+1:03d}"),
                    "project_name": extraction.extraction_text,
                    "aliases": attrs.get("aliases", []),
                    "status": attrs.get("status", "不明"),
                    "summary": attrs.get("summary", ""),
                    "last_updated": datetime.now().isoformat(),
                    "key_themes": attrs.get("key_themes", []),
                    "mentioned_people": attrs.get("people", []),
                    "information_snippets": related_snippets
                }
                projects.append(project)
        
        logger.info(f"統合完了: {len(projects)}個のプロジェクトを生成")
        
        result_data = {
            "unified_projects": projects,
            "extraction_metadata": {
                "processed_files": len(snippet_files),
                "timestamp": datetime.now().isoformat(),
                "model_used": self.model_id,
                "total_snippets": len([p["information_snippets"] for p in projects]),
                "projects_count": len(projects)
            }
        }
        
        # プロジェクト概要をログ出力
        for project in projects:
            logger.info(f"プロジェクト: {project['project_name']} ({project['status']})")
            logger.info(f"  エイリアス: {', '.join(project['aliases']) if project['aliases'] else 'なし'}")
            logger.info(f"  関連スニペット: {len(project['information_snippets'])}件")
            logger.info(f"  要約: {project['summary'][:100]}...")
        
        return result_data
    
    def _collect_related_snippets(self, project_name: str, aliases: List[str], 
                                 snippet_files: List[Path]) -> List[Dict[str, Any]]:
        """プロジェクトに関連するスニペットを収集（簡易版）."""
        related_snippets = []
        keywords = [project_name.lower()] + [alias.lower() for alias in aliases]
        
        # 主要キーワード（手動で定義）
        keyword_mapping = {
            "スマートタグ": ["スマートタグ", "smarttag", "smart tag", "タグ", "クラスタリング", "ハルシネーション"],
            "マルチデータソース": ["マルチデータソース", "multi data source", "データソース", "csv", "取り込み"]
        }
        
        for project_key, project_keywords in keyword_mapping.items():
            if any(keyword in project_name.lower() for keyword in [project_key.lower()]):
                keywords.extend([k.lower() for k in project_keywords])
        
        # ファイルからマッチするスニペットを収集
        for file_path in snippet_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            for extraction in data.get('extractions', []):
                                content = extraction.get('extraction_text', '').lower()
                                proj_keywords = extraction.get('attributes', {}).get('project_keywords', [])
                                proj_keywords_lower = [k.lower() for k in proj_keywords]
                                
                                # キーワードマッチング
                                if (any(keyword in content for keyword in keywords) or
                                    any(keyword in proj_keywords_lower for keyword in keywords)):
                                    
                                    snippet = {
                                        "content": extraction.get('extraction_text'),
                                        "source_url": file_path.name,
                                        "timestamp": datetime.now().isoformat(),
                                        "type": extraction.get('extraction_class')
                                    }
                                    related_snippets.append(snippet)
                                    
                        except (json.JSONDecodeError, KeyError):
                            continue
                            
            except Exception as e:
                logger.warning(f"スニペット収集でエラー {file_path}: {e}")
                continue
        
        # 重複除去と制限
        unique_snippets = []
        seen_content = set()
        for snippet in related_snippets[:20]:  # 最大20件
            if snippet["content"] not in seen_content:
                unique_snippets.append(snippet)
                seen_content.add(snippet["content"])
        
        logger.debug(f"関連スニペット収集: {len(unique_snippets)}件 (キーワード: {', '.join(keywords[:5])})")
        return unique_snippets