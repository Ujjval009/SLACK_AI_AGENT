from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from app.config import settings
from app.logger import log
from app.schemas import MemberInfo, ResearchResult, AnalysisResult
from app.research import do_basic_research
from app.llm import analyze_with_ai
from app import database
from app.models import MemberAnalysis

import json
import datetime


web_client = AsyncWebClient(token=settings.slack_bot_token)


async def get_user_info(user_id: str) -> MemberInfo:
    result = await web_client.users_info(user=user_id)
    user = result["user"]
    profile = user.get("profile", {})

    return MemberInfo(
        id=user["id"],
        name=profile.get("real_name") or user.get("name", ""),
        username=user.get("name"),
        email=profile.get("email"),
        title=profile.get("title"),
        timezone=user.get("tz"),
        profile={
            "firstName": profile.get("first_name"),
            "lastName": profile.get("last_name"),
            "statusText": profile.get("status_text"),
        },
    )


async def save_member_analysis(
    member_info: MemberInfo,
    analysis: AnalysisResult,
    research_data: list[ResearchResult],
) -> int:
    if database.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized")
    async with database.AsyncSessionLocal() as session:
        record = MemberAnalysis(
            member_id=member_info.id,
            member_name=member_info.name,
            member_email=member_info.email,
            member_title=member_info.title,
            member_timezone=member_info.timezone,
            fit_score=analysis.fitScore,
            insights=[i for i in analysis.insights],
            recommendations=[r for r in analysis.recommendations],
            research_data=[r.model_dump() for r in research_data],
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        log.info(f"Saved analysis to database with ID: {record.id}")
        return record.id


async def mark_as_sent_to_slack(analysis_id: int):
    if database.AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized")
    async with database.AsyncSessionLocal() as session:
        record = await session.get(MemberAnalysis, analysis_id)
        if record:
            record.sent_to_slack = True
            record.sent_to_slack_at = datetime.datetime.now(datetime.timezone.utc)
            await session.commit()


def _build_slack_blocks(member: MemberInfo, analysis: AnalysisResult) -> list[dict]:
    color = (
        "#36a64f" if analysis.fitScore >= 80
        else "#ffb84d" if analysis.fitScore >= 60
        else "#ff9500" if analysis.fitScore >= 40
        else "#ff4444"
    )

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"🔍 New Member: {member.name}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Fit Score:* {analysis.fitScore}/100"},
                {"type": "mrkdwn", "text": f"*Email:* {member.email or 'Not provided'}"},
                {"type": "mrkdwn", "text": f"*Title:* {member.title or 'Not provided'}"},
            ],
        },
    ]

    if analysis.insights:
        insights_text = "\n".join(f"• {i}" for i in analysis.insights)
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Insights:*\n{insights_text}"},
        })

    if analysis.recommendations:
        recs_text = "\n".join(f"• {r}" for r in analysis.recommendations)
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Recommendations:*\n{recs_text}"},
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"📊 Analyzed: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
            }
        ],
    })

    return [
        {
            "color": color,
            "blocks": blocks,
        }
    ]


async def post_analysis_to_channel(member: MemberInfo, analysis: AnalysisResult):
    attachments = _build_slack_blocks(member, analysis)
    await web_client.chat_postMessage(
        channel=settings.slack_private_channel_id,
        text=f"New Member Analysis: {member.name} ({analysis.fitScore}/100)",
        attachments=attachments,
    )
    log.info(f"Analysis posted to channel for {member.name}")


async def analyze_and_post_member(member_info: MemberInfo):
    analysis_id = None
    try:
        log.info(f"Processing member: {member_info.name}")
        research_data = await do_basic_research(member_info)
        analysis = await analyze_with_ai(member_info, research_data)

        log.info(f"Saving analysis to database for {member_info.name}")
        analysis_id = await save_member_analysis(member_info, analysis, research_data)

        await post_analysis_to_channel(member_info, analysis)

        if analysis_id:
            await mark_as_sent_to_slack(analysis_id)

    except Exception as e:
        log.error(f"Error processing {member_info.name}: {e}")
        if analysis_id:
            log.info(f"Analysis {analysis_id} saved to database but not sent to Slack due to error")
        raise


async def handle_socket_mode_request(client: SocketModeClient, req: SocketModeRequest):
    if req.type != "events_api":
        return

    payload = req.payload
    event = payload.get("event", {})

    if event.get("type") == "team_join":
        try:
            user_id = event["user"]["id"]
            log.info(f"New member joined: {event['user'].get('real_name') or event['user'].get('name')}")
            user_info = await get_user_info(user_id)
            await analyze_and_post_member(user_info)
        except Exception as e:
            log.error(f"Error processing team_join: {e}")

    elif event.get("type") == "member_joined_channel":
        try:
            channel_type = event.get("channel_type", "")
            if channel_type == "C":
                user_id = event["user"]
                log.info(f"Member {user_id} joined channel {event['channel']}")
                user_info = await get_user_info(user_id)
                await analyze_and_post_member(user_info)
        except Exception as e:
            log.error(f"Error processing member_joined_channel: {e}")


async def start_socket_mode():
    client = SocketModeClient(
        app_token=settings.slack_app_token,
        web_client=web_client,
    )
    client.socket_mode_request_listeners.append(handle_socket_mode_request)
    await client.connect()
    log.info("⚡️ Slack Socket Mode connected")
    return client
