"""Phase 2 execution script for project integration."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv

from pm_pedia_langextract.poc.extractors import IntegrationExtractor
from pm_pedia_langextract.utils.logging_config import setup_logging, get_logger

# 環境設定
load_dotenv()
setup_logging(level="INFO")
logger = get_logger(__name__)


def run_phase2() -> Dict[str, Any]:
    """フェーズ2: 統合・構造化処理."""
    logger.info("=== PM-pedia PoC Phase 2 開始 ===")
    
    # フェーズ1の出力ファイルを取得
    phase1_output_dir = Path("data/output/phase1")
    snippet_files = list(phase1_output_dir.glob("*_snippets.jsonl"))
    
    if not snippet_files:
        raise FileNotFoundError(
            "Phase 1の出力が見つかりません。先にPhase 1を実行してください。\n"
            f"期待するパス: {phase1_output_dir}/*_snippets.jsonl"
        )
    
    logger.info(f"統合対象ファイル: {len(snippet_files)}件")
    for f in snippet_files:
        logger.info(f"  - {f.name}")
    
    # 統合処理実行
    logger.info("統合抽出器を初期化中...")
    integrator = IntegrationExtractor()
    
    logger.info("統合処理を実行中...")
    result = integrator.extract(snippet_files)
    
    # 結果を保存
    output_dir = Path("data/output/phase2")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "unified_projects.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n=== Phase 2 完了 ===")
    logger.info(f"統合結果: {output_path}")
    logger.info(f"統合されたプロジェクト数: {len(result['unified_projects'])}")
    
    # 結果の詳細表示
    logger.info("\n--- 統合されたプロジェクト詳細 ---")
    for i, project in enumerate(result['unified_projects'], 1):
        logger.info(f"\n{i}. {project['project_name']} (ID: {project['project_id']})")
        logger.info(f"   ステータス: {project['status']}")
        
        if project['aliases']:
            logger.info(f"   別名: {', '.join(project['aliases'])}")
        
        if project['key_themes']:
            logger.info(f"   主要テーマ: {', '.join(project['key_themes'])}")
            
        if project['mentioned_people']:
            logger.info(f"   関係者: {', '.join(project['mentioned_people'])}")
        
        logger.info(f"   関連スニペット: {len(project['information_snippets'])}件")
        
        # サマリーを適切な長さで表示
        summary = project['summary']
        if len(summary) > 150:
            summary = summary[:147] + "..."
        logger.info(f"   要約: {summary}")
    
    # 抽出メタデータ表示
    metadata = result['extraction_metadata']
    logger.info(f"\n--- 処理統計 ---")
    logger.info(f"処理ファイル数: {metadata['processed_files']}")
    logger.info(f"使用モデル: {metadata['model_used']}")
    logger.info(f"処理時刻: {metadata['timestamp']}")
    
    return result


def analyze_results(result: Dict[str, Any]) -> None:
    """結果を分析して洞察を表示."""
    logger.info("\n=== 結果分析 ===")
    
    projects = result['unified_projects']
    
    # ステータス分布
    status_count = {}
    for project in projects:
        status = project['status']
        status_count[status] = status_count.get(status, 0) + 1
    
    logger.info("ステータス分布:")
    for status, count in status_count.items():
        logger.info(f"  {status}: {count}件")
    
    # 最も多くの人が関わっているプロジェクト
    if projects:
        max_people_project = max(projects, key=lambda p: len(p['mentioned_people']))
        if max_people_project['mentioned_people']:
            logger.info(f"\n最も多くの関係者が関わるプロジェクト:")
            logger.info(f"  {max_people_project['project_name']} ({len(max_people_project['mentioned_people'])}人)")
            logger.info(f"  関係者: {', '.join(max_people_project['mentioned_people'])}")
    
    # 最も多くのスニペットがあるプロジェクト
    if projects:
        max_snippets_project = max(projects, key=lambda p: len(p['information_snippets']))
        logger.info(f"\n最も多くの情報があるプロジェクト:")
        logger.info(f"  {max_snippets_project['project_name']} ({len(max_snippets_project['information_snippets'])}件)")


if __name__ == "__main__":
    try:
        result = run_phase2()
        analyze_results(result)
        
        logger.info("\n🎉 PM-pedia PoC Phase 2 が正常に完了しました！")
        logger.info("\n結果ファイル:")
        logger.info("  📊 data/output/phase2/unified_projects.json")
        logger.info("\n次のステップ:")
        logger.info("  1. 結果JSONファイルを確認")
        logger.info("  2. プロジェクトの名寄せ精度を評価")
        logger.info("  3. サマリーの質を確認")
        
    except Exception as e:
        logger.error("PoC Phase 2 でエラーが発生しました", exc_info=True)
        raise