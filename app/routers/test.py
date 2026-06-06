import datetime

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.logger import log
from app.schemas import TestAnalysisRequest, TestAnalysisResponse, MemberInfo
from app.research import do_basic_research
from app.llm import analyze_with_ai

router = APIRouter()


@router.post("/test/analyze-member", response_model=TestAnalysisResponse)
async def test_analyze_member(request: TestAnalysisRequest):
    if settings.node_env != "development":
        raise HTTPException(status_code=404, detail="Not found")

    member_info = request.memberInfo
    if not member_info:
        raise HTTPException(status_code=400, detail="memberInfo is required")

    try:
        log.info(f"Test analysis for member: {member_info.name}")
        research_data = await do_basic_research(member_info)
        analysis = await analyze_with_ai(member_info, research_data)

        return TestAnalysisResponse(
            success=True,
            analysis=analysis,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )
    except Exception as e:
        log.error(f"Test analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
