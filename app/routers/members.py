import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.logger import log
from app.models import MemberAnalysis
from app.schemas import UpdateTitleRequest, MemberUpdateResponse
from app.slack_client import get_user_info, post_analysis_to_channel
from app.research import do_basic_research
from app.llm import analyze_with_ai

router = APIRouter()


@router.patch("/members/{member_id}/title", response_model=MemberUpdateResponse)
async def update_member_title(member_id: str, request: UpdateTitleRequest):
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

    new_title = request.title.strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MemberAnalysis)
            .where(MemberAnalysis.member_id == member_id)
            .order_by(MemberAnalysis.analyzed_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for member {member_id}",
            )

        old_title = record.member_title

        member_info = await get_user_info(member_id)
        member_info.title = new_title

        research_data = await do_basic_research(member_info)
        analysis = await analyze_with_ai(member_info, research_data)

        record.member_title = new_title
        record.fit_score = analysis.fitScore
        record.insights = list(analysis.insights)
        record.recommendations = list(analysis.recommendations)
        record.research_data = [r.model_dump() for r in research_data]
        record.analyzed_at = datetime.datetime.now(datetime.timezone.utc)

        await session.commit()

        await post_analysis_to_channel(member_info, analysis)

        log.info(f"Re-analyzed member {member_id}: title '{old_title}' -> '{new_title}', "
                 f"fit score {analysis.fitScore}")

        return MemberUpdateResponse(
            success=True,
            message="Title updated and member re-analyzed successfully",
            member_id=member_id,
            title=new_title,
        )
