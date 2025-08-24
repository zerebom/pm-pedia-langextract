"""Few-shot examples for LangExtract."""

import langextract as lx
from typing import List


def get_triage_examples() -> List[lx.data.ExampleData]:
    """トリアージ用のFew-shotサンプルを返す."""
    return [
        lx.data.ExampleData(
            text="""# 週次レビュー 2025-W33
            
            ## 今週の成果
            - スマートタグ機能のPRDを完成させた
            - クラスタリングアルゴリズムの技術調査を完了
            
            ## 課題
            - データベースのパフォーマンスが想定より遅い
            - チームメンバーのAさんが体調不良で稼働率低下
            
            ## 来週の予定
            - クラスタリング機能の実装開始
            - パフォーマンス改善の対策検討""",
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
        ),
        lx.data.ExampleData(
            text="""# 2025-08-20
            
            ## 今日やったこと
            - 買い物に行った
            - ジムでトレーニング
            - 映画を見た
            
            ## 明日の予定  
            - 洗濯
            - 読書""",
            extractions=[
                lx.data.Extraction(
                    extraction_class="document_type",
                    extraction_text="個人的なメモ",
                    attributes={"confidence": "high"}
                ),
                lx.data.Extraction(
                    extraction_class="relevance_score",
                    extraction_text="0.1",
                    attributes={"reason": "PM業務と関係ない個人的な内容"}
                ),
                lx.data.Extraction(
                    extraction_class="summary",
                    extraction_text="個人的な日常活動の記録。PM業務との関連性なし。",
                    attributes={}
                )
            ]
        )
    ]


def get_snippet_extraction_examples() -> List[lx.data.ExampleData]:
    """スニペット抽出用のFew-shotサンプルを返す."""
    return [
        lx.data.ExampleData(
            text="""## 今週の成果
            - スマートタグ機能のPRDを完成させた
            - クラスタリングアルゴリズムの技術調査を完了
            - 青見さん、奥村さんとの1on1実施
            
            ## 課題
            - データベースのパフォーマンスが想定より遅い
            - チームメンバーのAさんが体調不良で稼働率低下
            
            ## 気づき
            - CSとプロダクトが近い環境でこそ生まれる、顧客の声の適切な優先順位付けが重要
            
            ## 次週のアクション
            - マルチデータソース対応のPRD作成を完遂する""",
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
                    extraction_class="進捗報告",
                    extraction_text="青見さん、奥村さんとの1on1実施",
                    attributes={
                        "project_keywords": [],
                        "people": ["青見さん", "奥村さん"]
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
                ),
                lx.data.Extraction(
                    extraction_class="気づき・インサイト",
                    extraction_text="CSとプロダクトが近い環境でこそ生まれる、顧客の声の適切な優先順位付けが重要",
                    attributes={
                        "project_keywords": ["CS", "プロダクト", "優先順位"],
                        "people": []
                    }
                ),
                lx.data.Extraction(
                    extraction_class="ネクストアクション",
                    extraction_text="マルチデータソース対応のPRD作成を完遂する",
                    attributes={
                        "project_keywords": ["マルチデータソース", "PRD"],
                        "people": []
                    }
                )
            ]
        ),
        lx.data.ExampleData(
            text="""## プロジェクト状況
            
            スマートタグのクラスタリング機能について、DBSCANアルゴリズムの採用を決定した。
            ただし、大規模データでの処理時間が懸念されるため、事前に性能テストが必要。
            
            小林さんと協議の結果、リリースまでに以下のブロッカーを解消することで合意：
            - クラスターの動的化
            - 料金と実行スピードの最適化
            
            来週、林さんにキーワード改善タスクを依頼予定。""",
            extractions=[
                lx.data.Extraction(
                    extraction_class="決定事項",
                    extraction_text="DBSCANアルゴリズムの採用を決定した",
                    attributes={
                        "project_keywords": ["スマートタグ", "クラスタリング", "DBSCAN"],
                        "people": []
                    }
                ),
                lx.data.Extraction(
                    extraction_class="リスク",
                    extraction_text="大規模データでの処理時間が懸念される",
                    attributes={
                        "project_keywords": ["大規模データ", "処理時間", "パフォーマンス"],
                        "people": []
                    }
                ),
                lx.data.Extraction(
                    extraction_class="決定事項",
                    extraction_text="小林さんと協議の結果、リリースまでに以下のブロッカーを解消することで合意",
                    attributes={
                        "project_keywords": ["リリース", "ブロッカー"],
                        "people": ["小林さん"]
                    }
                ),
                lx.data.Extraction(
                    extraction_class="課題",
                    extraction_text="クラスターの動的化",
                    attributes={
                        "project_keywords": ["クラスター", "動的化"],
                        "people": []
                    }
                ),
                lx.data.Extraction(
                    extraction_class="課題",
                    extraction_text="料金と実行スピードの最適化",
                    attributes={
                        "project_keywords": ["料金", "実行スピード", "最適化"],
                        "people": []
                    }
                ),
                lx.data.Extraction(
                    extraction_class="ネクストアクション",
                    extraction_text="来週、林さんにキーワード改善タスクを依頼予定",
                    attributes={
                        "project_keywords": ["キーワード", "改善"],
                        "people": ["林さん"]
                    }
                )
            ]
        )
    ]


def get_integration_examples() -> List[lx.data.ExampleData]:
    """統合・構造化用のFew-shotサンプルを返す."""
    return [
        lx.data.ExampleData(
            text="""[入力: 複数ドキュメントから抽出されたスニペット群]
            
            Document 1 (weekly_review_2025-W33.md):
            - 進捗報告: "スマートタグ機能のPRDを完成させた"
              Keywords: [スマートタグ, PRD]
            - 課題: "データベースのパフォーマンスが想定より遅い"
              Keywords: [データベース, パフォーマンス]
            
            Document 2 (smart_tag_clustering_prd_v1.md):
            - 決定事項: "クラスタリングアルゴリズムはDBSCANを採用"
              Keywords: [クラスタリング, DBSCAN]
            - リスク: "大規模データでの処理時間が懸念"
              Keywords: [大規模データ, 処理時間]
            
            Document 3 (journal_2025-08-23.md):
            - 気づき: "スマートタグのクラスタリング、思ったより複雑"
              Keywords: [スマートタグ, クラスタリング]""",
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