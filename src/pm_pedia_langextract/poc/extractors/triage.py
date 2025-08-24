"""Triage extractor for document analysis."""

import langextract as lx
from pathlib import Path
import textwrap
from typing import Tuple
from pm_pedia_langextract.poc.few_shot_examples import get_triage_examples
from pm_pedia_langextract.utils.logging_config import get_logger

logger = get_logger(__name__)


class TriageExtractor:
    """ドキュメントをトリアージして分析価値を判定する."""
    
    def __init__(self, model_id: str = "gemini-2.5-flash-lite"):
        self.model_id = model_id
        self.prompt = textwrap.dedent("""
            ドキュメントを分析し、以下の3つの要素を正確に抽出してください：
            
            1. document_type: ドキュメントの種類を以下から選択
               - 週次レビュー: 週単位の進捗レビューや振り返り
               - 技術仕様書: PRDやシステム設計書
               - 議事録: 会議の記録
               - 日報: 日々の作業記録
               - 個人的なメモ: プライベートな記録や雑記
               - その他: 上記に当てはまらないもの
               
            2. relevance_score: PM業務への関連度を0.0-1.0でスコアリング
               - 1.0: 完全にPM業務に関連（プロジェクト管理、進捗、課題等）
               - 0.5: 部分的に関連（技術的内容含む）
               - 0.0: 全く関連なし（個人的な内容のみ）
               
            3. summary: 内容を1-2文で簡潔に要約
            
            重要：必ず3つすべての要素を抽出し、元のテキストから正確に判断してください。
        """)
        self.examples = get_triage_examples()
    
    def extract(self, document_path: Path) -> Tuple[lx.data.AnnotatedDocument, float]:
        """ドキュメントをトリアージして分析価値を判定する.
        
        Args:
            document_path: 分析対象のドキュメントパス
            
        Returns:
            Tuple[AnnotatedDocument, relevance_score]: 抽出結果と関連度スコア
        """
        logger.info(f"トリアージ開始: {document_path.name}")
        
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            logger.debug(f"ドキュメント読み込み完了: {len(text)}文字")
            
            result = lx.extract(
                text_or_documents=text,
                prompt_description=self.prompt,
                examples=self.examples,
                model_id=self.model_id,
                extraction_passes=1,
                max_workers=1
            )
            
            # 関連度スコアを抽出
            relevance_score = 0.0
            for extraction in result.extractions:
                if extraction.extraction_class == "relevance_score":
                    try:
                        relevance_score = float(extraction.extraction_text)
                        break
                    except ValueError:
                        logger.warning(f"関連度スコアの変換に失敗: {extraction.extraction_text}")
            
            logger.info(f"トリアージ完了: {document_path.name}, スコア: {relevance_score}")
            return result, relevance_score
            
        except Exception as e:
            logger.error(f"トリアージ処理でエラー: {document_path.name}", exc_info=True)
            raise