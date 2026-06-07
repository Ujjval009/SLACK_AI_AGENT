import httpx
from typing import Optional

from app.logger import log
from app.schemas import ResearchResult


async def _search_web(query: str) -> Optional[ResearchResult]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                "https://lite.duckduckgo.com/lite/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if response.status_code == 200 and len(response.text) > 200:
                return ResearchResult(
                    url=f"https://duckduckgo.com/?q={query}",
                    title=f"Web search: {query}",
                    content=f"Found {len(response.text)} bytes of search results",
                    type="web_search",
                )
    except Exception as e:
        log.debug(f"Web search error: {e}")
    return None


def _get_profile_insights(member_info) -> list[str]:
    insights = []
    profile = member_info.profile or {}
    if profile.get("firstName") or profile.get("lastName"):
        name_parts = []
        if profile.get("firstName"):
            name_parts.append(profile["firstName"])
        if profile.get("lastName"):
            name_parts.append(profile["lastName"])
        insights.append(f"Display name: {' '.join(name_parts)}")
    if profile.get("displayName") and profile.get("displayName") != member_info.name:
        insights.append(f"Display name: {profile['displayName']}")
    if profile.get("statusText"):
        insights.append(f"Status: {profile['statusText']}")
    if profile.get("department"):
        insights.append(f"Department: {profile['department']}")
    if profile.get("team"):
        insights.append(f"Team: {profile['team']}")
    if profile.get("phone"):
        insights.append(f"Phone: {profile['phone']}")
    if member_info.timezone:
        insights.append(f"Timezone: {member_info.timezone}")
    if profile.get("skype"):
        insights.append(f"Skype: {profile['skype']}")
    return insights


async def do_basic_research(member_info) -> list[ResearchResult]:
    results: list[ResearchResult] = []
    try:
        profile_insights = _get_profile_insights(member_info)
        if profile_insights:
            results.append(ResearchResult(
                url="",
                title="Slack Profile",
                content=" | ".join(profile_insights),
                type="profile",
            ))

        if member_info.title:
            search_query = f"{member_info.name} {member_info.title}"
        elif member_info.name:
            search_query = member_info.name
        else:
            search_query = None

        if search_query:
            web_result = await _search_web(search_query)
            if web_result:
                results.append(web_result)

    except Exception as e:
        log.error(f"Research error: {e}")

    return results
