from pydantic import BaseModel, Field
from typing import List, Optional

class WebSearchResultItem(BaseModel):
    title: str = Field(..., description="Title of the web source")
    url: Optional[str] = Field(None, description="URL of the source")
    domain: str = Field(..., description="Domain name of the source")
    snippet: str = Field(..., description="Summary snippet from the source")
    published_date: Optional[str] = Field(None, description="Publication or update date")

class WebIntelligenceResponse(BaseModel):
    query: str = Field(..., description="Original search query")
    is_realtime_query: bool = Field(..., description="Whether real-time retrieval was triggered")
    answer: str = Field(..., description="Synthesized natural language answer")
    sources: List[WebSearchResultItem] = Field(default_factory=list, description="Verified source citations")
    confidence: float = Field(default=1.0, description="Confidence score")
