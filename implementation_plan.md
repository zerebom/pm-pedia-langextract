# PM-pedia PoC 実装計画書

## 概要

本ドキュメントは、PM-pediaの中核ロジックPoC（Proof of Concept）の実装計画を詳細に記述します。LangExtractライブラリを用いて、PMの非構造化ドキュメントから構造化データを抽出する3ステップ戦略の技術的実現可能性を検証します。

## 実装アーキテクチャ

### 技術スタック

- **言語**: Python 3.12+
- **主要ライブラリ**: 
  - `langextract`: LLMベースの情報抽出
  - `pydantic`: データモデル定義と検証
  - `python-dotenv`: 環境変数管理
- **LLMモデル**: 
  - メイン: Google Gemini 2.0 Flash (`gemini-2.0-flash-exp`)
  - 比較用: OpenAI GPT-4o (オプション)
- **開発ツール**: 
  - uv (パッケージ管理)
  - pytest (テスト)
  - Jupyter Notebook (実験・分析)

### ディレクトリ構造

```
pm-pedia-langextract/
├── src/pm_pedia_langextract/
│   ├── poc/
│   │   ├── __init__.py
│   │   ├── models/              # Pydanticモデル定義
│   │   │   ├── __init__.py
│   │   │   ├── triage.py        # トリアージ結果モデル
│   │   │   ├── snippet.py       # スニペット抽出モデル
│   │   │   └── integration.py   # 統合結果モデル
│   │   ├── extractors/          # 抽出ロジック
│   │   │   ├── __init__.py
│   │   │   ├── triage.py        # ステップ1: トリアージ
│   │   │   ├── snippet.py       # ステップ2: スニペット抽出
│   │   │   └── integration.py   # ステップ3: 統合・構造化
│   │   ├── few_shot_examples.py # Few-shotサンプル定義
│   │   └── main.py              # メイン実行スクリプト
├── data/
│   ├── sample_docs/             # テスト用ドキュメント
│   │   ├── weekly_review_2025-W33.md
│   │   ├── smart_tag_clustering_prd_v1.md
│   │   └── journal_2025-08-23.md
│   └── output/                  # 出力結果
│       ├── phase1/              # フェーズ1結果
│       └── phase2/              # フェーズ2結果
├── notebooks/
│   ├── 01_phase1_analysis.ipynb # フェーズ1分析
│   └── 02_phase2_analysis.ipynb # フェーズ2分析
├── tests/
│   └── test_poc.py
├── .env.example                 # 環境変数テンプレート
└── implementation_plan.md       # 本ドキュメント
```

## フェーズ1: 個別ドキュメント処理（1日目）

### 1.1 データモデル実装

#### triage.py
```python
from typing import Literal
from pydantic import BaseModel, Field

class TriageResult(BaseModel):
    """ドキュメントの分析価値を判定した結果"""
    document_type: Literal[
        "週次レビュー", "技術仕様書", "議事録", 
        "日報", "個人的なメモ", "その他"
    ] = Field(description="ドキュメントの種類")
    relevance_score: float = Field(
        description="PM業務への関連度スコア (0.0-1.0)",
        ge=0.0, le=1.0
    )
    summary: str = Field(description="ドキュメントの1-2文での要約")
```

#### snippet.py
```python
from typing import List, Literal
from pydantic import BaseModel, Field

class InformationSnippet(BaseModel):
    """ドキュメントから抽出された断片的な情報"""
    content: str = Field(description="元の文章からの引用テキスト")
    type: Literal[
        "課題", "決定事項", "リスク", 
        "進捗報告", "気づき・インサイト", "ネクストアクション"
    ] = Field(description="情報の種類")
    mentioned_people: List[str] = Field(
        description="言及された人物名のリスト", 
        default_factory=list
    )
    potential_project_keywords: List[str] = Field(
        description="関連しそうなプロジェクト名のキーワード", 
        default_factory=list
    )

class SnippetsExtractionResult(BaseModel):
    """1つのドキュメントから抽出されたスニペットのリスト"""
    source_document: str = Field(description="抽出元のドキュメントパス")
    information_snippets: List[InformationSnippet]
```

### 1.2 Few-shotサンプル設計

#### few_shot_examples.py
```python
import langextract as lx
from typing import List

def get_triage_examples() -> List[lx.data.ExampleData]:
    """トリアージ用のFew-shotサンプルを返す"""
    return [
        lx.data.ExampleData(
            text="""
            # 週次レビュー 2025-W33
            
            ## 今週の成果
            - スマートタグ機能のPRDを完成させた
            - クラスタリングアルゴリズムの技術調査を完了
            
            ## 課題
            - データベースのパフォーマンスが想定より遅い
            - チームメンバーのAさんが体調不良で稼働率低下
            
            ## 来週の予定
            - クラスタリング機能の実装開始
            - パフォーマンス改善の対策検討
            """,
            extractions=[
                lx.data.Extraction(
                    extraction_class="document_type",
                    extraction_text="週次レビュー",
                    attributes={"confidence": "high"}
                ),
                lx.data.Extraction(
                    extraction_class="relevance_score",
                    extraction_text="0.95",
                    attributes={"reason": "プロジェクト進捗と課題が明確"}
                ),
                lx.data.Extraction(
                    extraction_class="summary",
                    extraction_text="スマートタグ機能のPRD完成とクラスタリング調査を完了。DBパフォーマンスとメンバー稼働に課題あり。",
                    attributes={}
                )
            ]
        )
    ]

def get_snippet_extraction_examples() -> List[lx.data.ExampleData]:
    """スニペット抽出用のFew-shotサンプルを返す"""
    return [
        lx.data.ExampleData(
            text="""
            ## 今週の成果
            - スマートタグ機能のPRDを完成させた
            - クラスタリングアルゴリズムの技術調査を完了
            
            ## 課題
            - データベースのパフォーマンスが想定より遅い
            - チームメンバーのAさんが体調不良で稼働率低下
            """,
            extractions=[
                lx.data.Extraction(
                    extraction_class="進捗報告",
                    extraction_text="スマートタグ機能のPRDを完成させた",
                    attributes={
                        "project_keywords": ["スマートタグ", "PRD"],
                        "people": []
                    }
                ),
                lx.data.Extraction(
                    extraction_class="進捗報告",
                    extraction_text="クラスタリングアルゴリズムの技術調査を完了",
                    attributes={
                        "project_keywords": ["クラスタリング", "技術調査"],
                        "people": []
                    }
                ),
                lx.data.Extraction(
                    extraction_class="課題",
                    extraction_text="データベースのパフォーマンスが想定より遅い",
                    attributes={
                        "project_keywords": ["データベース", "パフォーマンス"],
                        "people": []
                    }
                ),
                lx.data.Extraction(
                    extraction_class="課題",
                    extraction_text="チームメンバーのAさんが体調不良で稼働率低下",
                    attributes={
                        "project_keywords": [],
                        "people": ["Aさん"]
                    }
                )
            ]
        )
    ]
```

### 1.3 抽出ロジック実装

#### extractors/triage.py
```python
import langextract as lx
from pathlib import Path
import textwrap
from ..few_shot_examples import get_triage_examples

class TriageExtractor:
    def __init__(self, model_id: str = "gemini-2.0-flash-exp"):
        self.model_id = model_id
        self.prompt = textwrap.dedent("""
            ドキュメントを分析し、以下を判定してください：
            
            1. document_type: ドキュメントの種類を分類
            2. relevance_score: PM業務への関連度を0.0-1.0でスコアリング
            3. summary: 内容を1-2文で要約
            
            重要：正確にテキストから判断し、必ず3つの要素を抽出してください。
        """)
        self.examples = get_triage_examples()
    
    def extract(self, document_path: Path) -> lx.data.AnnotatedDocument:
        """ドキュメントをトリアージして分析価値を判定"""
        with open(document_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        result = lx.extract(
            text_or_documents=text,
            prompt_description=self.prompt,
            examples=self.examples,
            model_id=self.model_id,
            extraction_passes=1,
            max_workers=1
        )
        
        return result
```

#### extractors/snippet.py
```python
import langextract as lx
from pathlib import Path
import textwrap
from ..few_shot_examples import get_snippet_extraction_examples

class SnippetExtractor:
    def __init__(self, model_id: str = "gemini-2.0-flash-exp"):
        self.model_id = model_id
        self.prompt = textwrap.dedent("""
            PMのドキュメントから重要な情報を抽出してください：
            
            抽出対象:
            - 課題: 問題や懸念事項
            - 決定事項: 決定された内容
            - リスク: 潜在的なリスク
            - 進捗報告: 完了したタスクや成果
            - 気づき・インサイト: 学びや発見
            - ネクストアクション: 今後の予定やTODO
            
            各抽出には以下の属性を付与:
            - project_keywords: 関連プロジェクトのキーワード
            - people: 言及された人物名
            
            重要: 元のテキストから正確に引用し、パラフレーズしないでください。
        """)
        self.examples = get_snippet_extraction_examples()
    
    def extract(self, document_path: Path) -> lx.data.AnnotatedDocument:
        """ドキュメントから情報スニペットを抽出"""
        with open(document_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        result = lx.extract(
            text_or_documents=text,
            prompt_description=self.prompt,
            examples=self.examples,
            model_id=self.model_id,
            extraction_passes=2,  # 複数パスで精度向上
            max_workers=5,
            max_char_buffer=1500  # 適切なチャンクサイズ
        )
        
        return result
```

### 1.4 メイン実行スクリプト（フェーズ1）

#### main.py (フェーズ1部分)
```python
import os
from pathlib import Path
from dotenv import load_dotenv
import langextract as lx
import json
from .extractors.triage import TriageExtractor
from .extractors.snippet import SnippetExtractor

load_dotenv()

def run_phase1():
    """フェーズ1: 個別ドキュメント処理"""
    
    # 環境変数確認
    api_key = os.getenv("LANGEXTRACT_API_KEY")
    if not api_key:
        raise ValueError("LANGEXTRACT_API_KEY環境変数が設定されていません")
    
    # サンプルドキュメントのパス
    sample_docs = [
        "data/sample_docs/weekly_review_2025-W33.md",
        "data/sample_docs/smart_tag_clustering_prd_v1.md",
        "data/sample_docs/journal_2025-08-23.md"
    ]
    
    triage_extractor = TriageExtractor()
    snippet_extractor = SnippetExtractor()
    
    results = []
    
    for doc_path in sample_docs:
        doc_path = Path(doc_path)
        print(f"\n処理中: {doc_path.name}")
        
        # ステップ1: トリアージ
        print("  - トリアージ実行中...")
        triage_result = triage_extractor.extract(doc_path)
        
        # トリアージ結果を解析
        relevance_score = 0.0
        for extraction in triage_result.extractions:
            if extraction.extraction_class == "relevance_score":
                relevance_score = float(extraction.extraction_text)
                break
        
        # 関連度が0.7以上の場合のみスニペット抽出
        if relevance_score >= 0.7:
            print(f"  - 関連度スコア: {relevance_score} - スニペット抽出を実行")
            snippet_result = snippet_extractor.extract(doc_path)
            
            # 結果を保存
            output_path = Path(f"data/output/phase1/{doc_path.stem}_snippets.jsonl")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            lx.io.save_annotated_documents([snippet_result], output_name=str(output_path))
            
            # 可視化HTML生成
            html_content = lx.visualize(str(output_path))
            html_path = output_path.with_suffix('.html')
            with open(html_path, 'w') as f:
                f.write(html_content)
            
            print(f"  - 結果を保存: {output_path}")
            print(f"  - 可視化HTML: {html_path}")
            
            results.append({
                "document": doc_path.name,
                "relevance_score": relevance_score,
                "snippets_count": len(snippet_result.extractions),
                "output_file": str(output_path)
            })
        else:
            print(f"  - 関連度スコア: {relevance_score} - スキップ")
    
    # サマリー出力
    summary_path = Path("data/output/phase1/summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nフェーズ1完了。サマリー: {summary_path}")
    return results

if __name__ == "__main__":
    run_phase1()
```

## フェーズ2: 統合・構造化（2日目）

### 2.1 統合モデル定義

#### models/integration.py
```python
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class UnifiedInformationSnippet(BaseModel):
    """統合・構造化された情報スニペット"""
    content: str = Field(description="元の文章からの引用テキスト")
    source_url: str = Field(description="引用元ドキュメントへのパス")
    timestamp: Optional[datetime] = Field(description="引用元ドキュメントの日付")
    type: Literal[
        "課題", "決定事項", "リスク", 
        "進捗報告", "気づき・インサイト", "ネクストアクション"
    ] = Field(description="情報の種類")

class UnifiedProject(BaseModel):
    """最終的に生成される、単一プロジェクトに関する集約情報"""
    project_id: str = Field(description="AIが割り振る一意のID")
    project_name: str = Field(description="名寄せ・統合された代表プロジェクト名")
    aliases: List[str] = Field(
        description="AIが同一と判断した別名のリスト", 
        default_factory=list
    )
    status: Literal["順調", "停滞", "要確認", "完了", "不明"] = Field(
        description="AIが推定する最新のステータス"
    )
    summary: str = Field(description="AIによるプロジェクトの現状サマリー")
    last_updated: datetime = Field(description="関連情報が最後に見つかった日時")
    key_themes: List[str] = Field(
        description="プロジェクトの主要テーマ（タグ）", 
        default_factory=list
    )
    mentioned_people: List[str] = Field(
        description="プロジェクトに関連して言及された人物", 
        default_factory=list
    )
    information_snippets: List[UnifiedInformationSnippet] = Field(
        description="時系列にソートされた関連スニペット"
    )

class IntegrationResult(BaseModel):
    """PoCの最終的なアウトプット"""
    unified_projects: List[UnifiedProject]
    extraction_metadata: dict = Field(
        description="抽出プロセスのメタデータ",
        default_factory=dict
    )
```

### 2.2 統合用Few-shotサンプル

```python
def get_integration_examples() -> List[lx.data.ExampleData]:
    """統合・構造化用のFew-shotサンプルを返す"""
    return [
        lx.data.ExampleData(
            text="""
            [入力: 複数ドキュメントから抽出されたスニペット群]
            
            Document 1 (weekly_review_2025-W33.md):
            - 進捗報告: "スマートタグ機能のPRDを完成させた"
            - 課題: "データベースのパフォーマンスが想定より遅い"
            
            Document 2 (smart_tag_clustering_prd_v1.md):
            - 決定事項: "クラスタリングアルゴリズムはDBSCANを採用"
            - リスク: "大規模データでの処理時間が懸念"
            
            Document 3 (journal_2025-08-23.md):
            - 気づき: "スマートタグのクラスタリング、思ったより複雑"
            """,
            extractions=[
                lx.data.Extraction(
                    extraction_class="project",
                    extraction_text="スマートタグ・クラスタリング機能",
                    attributes={
                        "project_id": "proj_001",
                        "aliases": ["スマートタグ", "クラスタリング機構", "タグクラスタリング"],
                        "status": "要確認",
                        "summary": "PRDは完成したが、パフォーマンス課題があり実装に懸念。DBSCANアルゴリズムを採用予定。",
                        "key_themes": ["機械学習", "パフォーマンス最適化", "データベース"],
                        "people": []
                    }
                )
            ]
        )
    ]
```

### 2.3 統合ロジック実装

#### extractors/integration.py
```python
import langextract as lx
from pathlib import Path
import textwrap
import json
from typing import List, Dict, Any
from datetime import datetime

class IntegrationExtractor:
    def __init__(self, model_id: str = "gemini-2.0-flash-exp"):
        self.model_id = model_id
        self.prompt = textwrap.dedent("""
            複数のドキュメントから抽出されたスニペット群を分析し、
            プロジェクト単位で情報を統合・構造化してください。
            
            タスク:
            1. 同一プロジェクトを指す異なる表現を名寄せ
            2. プロジェクトごとに情報を集約
            3. 現在のステータスを推定
            4. 包括的なサマリーを生成
            
            出力形式:
            - project_id: 一意のID (proj_XXX形式)
            - project_name: 統一されたプロジェクト名
            - aliases: 名寄せした別名リスト
            - status: 現在の状態
            - summary: プロジェクトの現状説明
            - key_themes: 主要なテーマやタグ
            - people: 関連する人物
            
            重要: 類似した名前のプロジェクトは同一として扱い、
            情報を統合してください。
        """)
    
    def load_snippets(self, snippet_files: List[Path]) -> str:
        """複数のスニペットファイルを読み込んで統合"""
        all_snippets = []
        
        for file_path in snippet_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line)
                    doc_name = Path(data.get('text', '')).name
                    
                    for extraction in data.get('extractions', []):
                        snippet_info = {
                            'document': doc_name,
                            'type': extraction.get('extraction_class'),
                            'content': extraction.get('extraction_text'),
                            'attributes': extraction.get('attributes', {})
                        }
                        all_snippets.append(snippet_info)
        
        # テキスト形式に変換
        text_output = "抽出されたスニペット一覧:\n\n"
        current_doc = None
        
        for snippet in all_snippets:
            if snippet['document'] != current_doc:
                current_doc = snippet['document']
                text_output += f"\n[Document: {current_doc}]\n"
            
            text_output += f"- {snippet['type']}: \"{snippet['content']}\"\n"
            if snippet['attributes'].get('project_keywords'):
                text_output += f"  Keywords: {', '.join(snippet['attributes']['project_keywords'])}\n"
            if snippet['attributes'].get('people'):
                text_output += f"  People: {', '.join(snippet['attributes']['people'])}\n"
        
        return text_output
    
    def extract(self, snippet_files: List[Path]) -> Dict[str, Any]:
        """スニペットファイルから統合データを生成"""
        
        # スニペットを統合テキストに変換
        integrated_text = self.load_snippets(snippet_files)
        
        # LangExtractで統合処理
        result = lx.extract(
            text_or_documents=integrated_text,
            prompt_description=self.prompt,
            examples=get_integration_examples(),
            model_id=self.model_id,
            extraction_passes=1,
            max_workers=1
        )
        
        # 結果を構造化
        projects = []
        for extraction in result.extractions:
            if extraction.extraction_class == "project":
                attrs = extraction.attributes or {}
                project = {
                    "project_id": attrs.get("project_id", "unknown"),
                    "project_name": extraction.extraction_text,
                    "aliases": attrs.get("aliases", []),
                    "status": attrs.get("status", "不明"),
                    "summary": attrs.get("summary", ""),
                    "last_updated": datetime.now().isoformat(),
                    "key_themes": attrs.get("key_themes", []),
                    "mentioned_people": attrs.get("people", []),
                    "information_snippets": []  # 後で追加実装
                }
                projects.append(project)
        
        return {
            "unified_projects": projects,
            "extraction_metadata": {
                "processed_files": len(snippet_files),
                "timestamp": datetime.now().isoformat(),
                "model_used": self.model_id
            }
        }
```

### 2.4 メイン実行スクリプト（フェーズ2）

```python
def run_phase2():
    """フェーズ2: 統合・構造化"""
    
    # フェーズ1の出力ファイルを取得
    phase1_output_dir = Path("data/output/phase1")
    snippet_files = list(phase1_output_dir.glob("*_snippets.jsonl"))
    
    if not snippet_files:
        print("フェーズ1の出力が見つかりません。先にフェーズ1を実行してください。")
        return
    
    print(f"統合対象ファイル: {len(snippet_files)}件")
    for f in snippet_files:
        print(f"  - {f.name}")
    
    # 統合処理実行
    integrator = IntegrationExtractor()
    result = integrator.extract(snippet_files)
    
    # 結果を保存
    output_path = Path("data/output/phase2/unified_projects.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nフェーズ2完了。統合結果: {output_path}")
    print(f"統合されたプロジェクト数: {len(result['unified_projects'])}")
    
    for project in result['unified_projects']:
        print(f"\n- {project['project_name']} ({project['status']})")
        print(f"  {project['summary']}")
    
    return result
```

## 実装スケジュール

### Day 1: フェーズ1実装とテスト

| 時間 | タスク | 成果物 |
|------|--------|--------|
| 09:00-10:00 | 環境セットアップ、依存関係インストール | .env設定完了 |
| 10:00-11:30 | データモデル実装 | models/*.py |
| 11:30-13:00 | Few-shotサンプル設計 | few_shot_examples.py |
| 14:00-16:00 | 抽出ロジック実装 | extractors/triage.py, snippet.py |
| 16:00-17:00 | フェーズ1テスト実行 | phase1出力ファイル |
| 17:00-18:00 | 結果分析、改善点抽出 | 分析ノートブック |

### Day 2: フェーズ2実装と評価

| 時間 | タスク | 成果物 |
|------|--------|--------|
| 09:00-10:30 | 統合モデル実装 | models/integration.py |
| 10:30-12:00 | 統合ロジック実装 | extractors/integration.py |
| 13:00-14:30 | フェーズ2テスト実行 | unified_projects.json |
| 14:30-16:00 | 全体評価、精度測定 | 評価レポート |
| 16:00-17:30 | ドキュメント作成 | poc_report.md |
| 17:30-18:00 | 次ステップの検討 | 改善提案書 |

## 評価基準

### フェーズ1評価項目

1. **トリアージ精度**
   - ドキュメント種別の正確な分類
   - 関連度スコアの妥当性
   - サマリーの質

2. **スニペット抽出品質**
   - 抽出漏れの少なさ（再現率）
   - 誤抽出の少なさ（適合率）
   - 分類の正確性

3. **技術的側面**
   - 処理時間
   - エラーハンドリング
   - 出力形式の正確性

### フェーズ2評価項目

1. **名寄せ精度**
   - 同一プロジェクトの正しい統合
   - 異なるプロジェクトの誤統合回避

2. **サマリー品質**
   - 情報の網羅性
   - 論理的な一貫性
   - 実用性

3. **スケーラビリティ**
   - 大量ドキュメント処理能力
   - APIコスト効率

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| API制限・レート制限 | 高 | バックオフ戦略実装、ローカルモデル準備 |
| Few-shotサンプルの品質不足 | 高 | 反復的な改善、複数バリエーション準備 |
| 日本語処理の精度問題 | 中 | 日本語特化プロンプト調整 |
| 名寄せの過剰統合 | 中 | 閾値調整、人間による確認フロー |
| コスト超過 | 低 | 使用量モニタリング、上限設定 |

## 次のステップ

PoC成功後の展開計画：

1. **精度向上**
   - Few-shotサンプルの拡充
   - プロンプトエンジニアリング最適化
   - モデル比較評価（GPT-4o, Claude等）

2. **機能拡張**
   - リアルタイムデータソース連携
   - インクリメンタル更新
   - ユーザーフィードバック反映

3. **プロダクト化**
   - Web UIの実装
   - データベース永続化
   - 認証・認可機能

## 必要なリソース

- **API Key**: Google Gemini API（必須）
- **サンプルデータ**: 実際のPMドキュメント3-5件
- **計算リソース**: 標準的な開発マシン
- **推定APIコスト**: $5-10（PoC期間中）

## まとめ

本実装計画は、PM-pediaの中核となる情報抽出・構造化機能の技術的実現可能性を2日間で検証します。LangExtractの強力な抽出機能とFew-shot学習を活用し、段階的なアプローチで精度の高い構造化データ生成を目指します。

成功基準は「人間が手動では気づけなかった非自明で実用的な洞察を1つ以上提供できること」であり、この目標達成に向けて体系的に実装を進めます。