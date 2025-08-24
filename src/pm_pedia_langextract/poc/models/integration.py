"""Integration and unification models."""

from typing import List, Literal, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UnifiedInformationSnippet(BaseModel):
    """統合・構造化された情報スニペット."""
    
    content: str = Field(
        description="元の文章からの引用テキスト"
    )
    
    source_url: str = Field(
        description="引用元ドキュメントへのパス"
    )
    
    timestamp: Optional[datetime] = Field(
        description="引用元ドキュメントの日付",
        default=None
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


class UnifiedProject(BaseModel):
    """最終的に生成される、単一プロジェクトに関する集約情報."""
    
    project_id: str = Field(
        description="AIが割り振る一意のID"
    )
    
    project_name: str = Field(
        description="名寄せ・統合された代表プロジェクト名"
    )
    
    aliases: List[str] = Field(
        description="AIが同一と判断した別名のリスト", 
        default_factory=list
    )
    
    status: Literal["順調", "停滞", "要確認", "完了", "不明"] = Field(
        description="AIが推定する最新のステータス"
    )
    
    summary: str = Field(
        description="AIによるプロジェクトの現状サマリー"
    )
    
    last_updated: datetime = Field(
        description="関連情報が最後に見つかった日時"
    )
    
    key_themes: List[str] = Field(
        description="プロジェクトの主要テーマ（タグ）", 
        default_factory=list
    )
    
    mentioned_people: List[str] = Field(
        description="プロジェクトに関連して言及された人物", 
        default_factory=list
    )
    
    information_snippets: List[UnifiedInformationSnippet] = Field(
        description="時系列にソートされた関連スニペット",
        default_factory=list
    )


class IntegrationResult(BaseModel):
    """PoCの最終的なアウトプット."""
    
    unified_projects: List[UnifiedProject] = Field(
        description="統合されたプロジェクトリスト"
    )
    
    extraction_metadata: dict = Field(
        description="抽出プロセスのメタデータ",
        default_factory=dict
    )