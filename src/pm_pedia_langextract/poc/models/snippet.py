"""Snippet extraction models."""

from typing import List, Literal
from pydantic import BaseModel, Field


class InformationSnippet(BaseModel):
    """ドキュメントから抽出された断片的な情報."""
    
    content: str = Field(
        description="元の文章からの引用テキスト"
    )
    
    type: Literal[
        "課題", 
        "決定事項", 
        "リスク", 
        "進捗報告", 
        "気づき・インサイト", 
        "ネクストアクション"
    ] = Field(
        description="情報の種類"
    )
    
    mentioned_people: List[str] = Field(
        description="言及された人物名のリスト", 
        default_factory=list
    )
    
    potential_project_keywords: List[str] = Field(
        description="関連しそうなプロジェクト名のキーワード", 
        default_factory=list
    )


class SnippetsExtractionResult(BaseModel):
    """1つのドキュメントから抽出されたスニペットのリスト."""
    
    source_document: str = Field(
        description="抽出元のドキュメントパス"
    )
    
    information_snippets: List[InformationSnippet] = Field(
        description="抽出されたスニペット"
    )