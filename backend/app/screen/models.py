from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ScreenCaptureMetadata(BaseModel):
    width: int = Field(..., description="Screen width in pixels")
    height: int = Field(..., description="Screen height in pixels")
    timestamp: str = Field(..., description="Capture timestamp ISO string")
    format: str = Field(default="PNG", description="Image format")

class ScreenAnalyzeRequest(BaseModel):
    question: Optional[str] = Field(None, description="Specific question regarding the screen content")
    language: Optional[str] = Field("en", description="Preferred response language code (en, bn, hi)")

class ScreenAnalyzeResponse(BaseModel):
    success: bool = Field(..., description="Whether screen capture and analysis succeeded")
    language: str = Field(default="en", description="Response language")
    summary: str = Field(..., description="Natural language summary of visible screen content")
    details: Optional[str] = Field(None, description="Detailed explanation or step-by-step breakdown")
    visible_text: Optional[str] = Field(None, description="Notable text or error messages visible on screen")
    detected_elements: List[str] = Field(default_factory=list, description="High-level visible UI windows/elements")
    errors_or_warnings: Optional[str] = Field(None, description="Detected visible errors or diagnostic warnings")
    provider: str = Field(default="Unconfigured", description="Vision provider used")
    timestamp: str = Field(..., description="Analysis timestamp")
