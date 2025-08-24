"""Main execution script for PM-pedia PoC."""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
import langextract as lx

from pm_pedia_langextract.poc.extractors import TriageExtractor, SnippetExtractor
from pm_pedia_langextract.utils.logging_config import setup_logging, get_logger

# 環境設定
load_dotenv()
setup_logging(level="INFO")
logger = get_logger(__name__)


def run_phase1() -> List[Dict[str, Any]]:
    """フェーズ1: 個別ドキュメント処理."""
    logger.info("=== PM-pedia PoC Phase 1 開始 ===")
    
    # 環境変数確認
    api_key = os.getenv("LANGEXTRACT_API_KEY")
    if not api_key:
        raise ValueError(
            "LANGEXTRACT_API_KEY環境変数が設定されていません。\n"
            ".env ファイルを作成し、Gemini APIキーを設定してください。"
        )
    
    # サンプルドキュメントのパス
    sample_docs = [
        Path("data/sample_docs/weekly_review_2025-W33.md"),
        Path("data/sample_docs/smart_tag_clustering_prd_v1.md"),
        Path("data/sample_docs/journal_2025-08-23.md")
    ]
    
    # 存在確認
    for doc_path in sample_docs:
        if not doc_path.exists():
            raise FileNotFoundError(f"サンプルドキュメントが見つかりません: {doc_path}")
    
    # 抽出器の初期化
    logger.info("抽出器を初期化中...")
    triage_extractor = TriageExtractor()
    snippet_extractor = SnippetExtractor()
    
    results = []
    
    for doc_path in sample_docs:
        logger.info(f"\n--- 処理中: {doc_path.name} ---")
        
        # ステップ1: トリアージ
        logger.info("ステップ1: トリアージ実行中...")
        triage_result, relevance_score = triage_extractor.extract(doc_path)
        
        # トリアージ結果を解析して表示
        document_type = "不明"
        summary = "取得できませんでした"
        
        for extraction in triage_result.extractions:
            if extraction.extraction_class == "document_type":
                document_type = extraction.extraction_text
            elif extraction.extraction_class == "summary":
                summary = extraction.extraction_text
        
        logger.info(f"  文書種別: {document_type}")
        logger.info(f"  関連度スコア: {relevance_score}")
        logger.info(f"  要約: {summary}")
        
        # 関連度が0.7以上の場合のみスニペット抽出
        if relevance_score >= 0.7:
            logger.info(f"  関連度スコア: {relevance_score} >= 0.7 - スニペット抽出を実行")
            
            # ステップ2: スニペット抽出
            snippet_result = snippet_extractor.extract(doc_path)
            
            # 結果を保存
            output_dir = Path("data/output/phase1")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_name = f"{doc_path.stem}_snippets"
            
            lx.io.save_annotated_documents(
                [snippet_result], 
                output_name=output_name,
                output_dir=str(output_dir)
            )
            
            # LangExtractは拡張子なしで保存するため、リネーム
            temp_path = output_dir / output_name
            output_path = output_dir / f"{output_name}.jsonl"
            if temp_path.exists() and not output_path.exists():
                temp_path.rename(output_path)
            
            # 可視化HTML生成
            html_content = lx.visualize(str(output_path))
            html_path = output_path.with_suffix('.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"  結果を保存: {output_path}")
            logger.info(f"  可視化HTML: {html_path}")
            
            # 結果サマリー
            extraction_types = {}
            for extraction in snippet_result.extractions:
                ext_type = extraction.extraction_class
                extraction_types[ext_type] = extraction_types.get(ext_type, 0) + 1
            
            logger.info(f"  抽出サマリー: {extraction_types}")
            
            results.append({
                "document": doc_path.name,
                "document_type": document_type,
                "relevance_score": relevance_score,
                "summary": summary,
                "snippets_count": len(snippet_result.extractions),
                "snippets_by_type": extraction_types,
                "output_file": str(output_path),
                "html_file": str(html_path),
                "processed": True
            })
        else:
            logger.info(f"  関連度スコア: {relevance_score} < 0.7 - スニペット抽出をスキップ")
            results.append({
                "document": doc_path.name,
                "document_type": document_type,
                "relevance_score": relevance_score,
                "summary": summary,
                "snippets_count": 0,
                "snippets_by_type": {},
                "output_file": None,
                "html_file": None,
                "processed": False
            })
    
    # サマリー出力
    summary_path = Path("data/output/phase1/phase1_summary.json")
    summary_data = {
        "execution_time": datetime.now().isoformat(),
        "total_documents": len(sample_docs),
        "processed_documents": len([r for r in results if r["processed"]]),
        "results": results
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n=== Phase 1 完了 ===")
    logger.info(f"処理文書数: {len(results)}")
    logger.info(f"スニペット抽出対象: {len([r for r in results if r['processed']])}件")
    logger.info(f"サマリーファイル: {summary_path}")
    
    # 結果の詳細表示
    logger.info("\n--- 詳細結果 ---")
    for result in results:
        logger.info(f"{result['document']}:")
        logger.info(f"  種別: {result['document_type']}, スコア: {result['relevance_score']}")
        if result['processed']:
            logger.info(f"  抽出件数: {result['snippets_count']}")
            for type_name, count in result['snippets_by_type'].items():
                logger.info(f"    {type_name}: {count}件")
        else:
            logger.info("  処理スキップ")
    
    return results


if __name__ == "__main__":
    try:
        results = run_phase1()
        logger.info("PoC Phase 1 が正常に完了しました")
        
        # 次のステップの案内
        processed_count = len([r for r in results if r["processed"]])
        if processed_count > 0:
            logger.info(f"\n次のステップ:")
            logger.info(f"Phase 2を実行するには以下を実行してください:")
            logger.info(f"uv run python -m src.pm_pedia_langextract.poc.main_phase2")
        
    except Exception as e:
        logger.error("PoC Phase 1 でエラーが発生しました", exc_info=True)
        raise