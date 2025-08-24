"""Snippet extractor for information extraction."""

import langextract as lx
from pathlib import Path
import textwrap
from pm_pedia_langextract.poc.few_shot_examples import get_snippet_extraction_examples
from pm_pedia_langextract.utils.logging_config import get_logger

logger = get_logger(__name__)


class SnippetExtractor:
    """ドキュメントから情報スニペットを抽出する."""
    
    def __init__(self, model_id: str = "gemini-2.5-flash-lite"):
        self.model_id = model_id
        self.prompt = textwrap.dedent("""
            PMのドキュメントから重要な情報を以下のカテゴリで抽出してください：
            
            抽出対象のカテゴリ:
            - 課題: 問題や懸念事項、解決が必要な事項
            - 決定事項: 決定された内容、合意事項
            - リスク: 潜在的なリスク、懸念される問題
            - 進捗報告: 完了したタスクや成果、達成事項
            - 気づき・インサイト: 学びや発見、新しい洞察
            - ネクストアクション: 今後の予定やTODO、計画
            
            抽出ルール:
            1. 元のテキストから正確に引用し、パラフレーズしない
            2. 各抽出には以下の属性を付与:
               - project_keywords: 関連するプロジェクト名やキーワード
               - people: 言及された人物名（「さん」「氏」等の敬称込み）
            3. 文脈から明確に読み取れる情報のみ抽出
            4. 一つの文に複数の情報が含まれる場合は適切に分割
            
            重要: 情報の価値が高く、後で参照する際に有用なものを優先的に抽出してください。
        """)
        self.examples = get_snippet_extraction_examples()
    
    def extract(self, document_path: Path) -> lx.data.AnnotatedDocument:
        """ドキュメントから情報スニペットを抽出する.
        
        Args:
            document_path: 抽出対象のドキュメントパス
            
        Returns:
            AnnotatedDocument: 抽出結果
        """
        logger.info(f"スニペット抽出開始: {document_path.name}")
        
        try:
            with open(document_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            logger.debug(f"ドキュメント読み込み完了: {len(text)}文字")
            
            result = lx.extract(
                text_or_documents=text,
                prompt_description=self.prompt,
                examples=self.examples,
                model_id=self.model_id,
                extraction_passes=2,  # 複数パスで精度向上
                max_workers=5,
                max_char_buffer=1500  # 適切なチャンクサイズ
            )
            
            logger.info(f"スニペット抽出完了: {document_path.name}, {len(result.extractions)}件")
            
            # 抽出結果のサマリーを出力
            extraction_summary = {}
            for extraction in result.extractions:
                category = extraction.extraction_class
                extraction_summary[category] = extraction_summary.get(category, 0) + 1
            
            logger.info(f"抽出結果サマリー: {extraction_summary}")
            
            return result
            
        except Exception as e:
            logger.error(f"スニペット抽出でエラー: {document_path.name}", exc_info=True)
            raise