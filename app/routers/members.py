from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.logger import log
from app.models import MemberAnalysis
from app.schemas import UpdateTitleRequest, MemberUpdateResponse

router = APIRouter()


@router.patch("/members/{member_id}/title", response_model=MemberUpdateResponse)
async def update_member_title(member_id: str, request: UpdateTitleRequest):
    if AsyncSessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not initialized")

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
        record.member_title = request.title
        await session.commit()

        log.info(f"Updated title for member {member_id}: '{old_title}' -> '{request.title}'")

        return MemberUpdateResponse(
            success=True,
            message="Title updated successfully",
            member_id=member_id,
            title=request.title,
        )
