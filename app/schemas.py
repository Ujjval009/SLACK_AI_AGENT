from pydantic import BaseModel
from typing import Optional


class MemberInfo(BaseModel):
    id: Optional[str] = None
    name: str
    username: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    timezone: Optional[str] = None
    profile: Optional[dict] = None


class ResearchResult(BaseModel):
    url: str
    title: str
    content: str
    type: str


class AnalysisResult(BaseModel):
    fitScore: int
    insights: list[str]
    recommendations: list[str]


class HealthResponse(BaseModel):
    status: str
    timestamp: str


class TestAnalysisRequest(BaseModel):
    memberInfo: MemberInfo


class TestAnalysisResponse(BaseModel):
    success: bool
    analysis: AnalysisResult
    timestamp: str
