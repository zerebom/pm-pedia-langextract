"""Triage result model for document analysis."""

from typing import Literal
from pydantic import BaseModel, Field


class TriageResult(BaseModel):
    """ドキュメントの分析価値を判定した結果."""
    
    document_type: Literal[
        "週次レビュー", 
        "技術仕様書", 
        "議事録", 
        "日報", 
        "個人的なメモ", 
        "その他"
    ] = Field(description="ドキュメントの種類")
    
    relevance_score: float = Field(
        description="PM業務への関連度スコア (0.0-1.0)",
        ge=0.0, 
        le=1.0
    )
    
    summary: str = Field(
        description="ドキュメントの1-2文での要約"
    )