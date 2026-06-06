import httpx
import re
from typing import Optional

from app.logger import log
from app.schemas import ResearchResult

PERSONAL_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com",
    "outlook.com", "icloud.com",
}


def is_personal_email(email: str) -> bool:
    domain = email.split("@")[-1].lower() if "@" in email else ""
    return domain in PERSONAL_EMAIL_DOMAINS


async def get_company_info(domain: str) -> Optional[ResearchResult]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"https://www.{domain}",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            title_match = re.search(r"<title>(.*?)</title>", response.text, re.IGNORECASE)
            title = title_match.group(1) if title_match else f"Company: {domain}"
            return ResearchResult(
                url=f"https://www.{domain}",
                title=title,
                content=f"Company website for {domain}",
                type="company",
            )
    except Exception as e:
        log.debug(f"Could not fetch {domain}: {e}")
        return None


async def get_github_info(name: str) -> Optional[ResearchResult]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"https://api.github.com/search/users?q={name}",
            )
            data = response.json()
            items = data.get("items", [])
            if items:
                user = items[0]
                return ResearchResult(
                    url=user["html_url"],
                    title=f"GitHub: {user['login']}",
                    content=f"{user['public_repos']} public repositories",
                    type="github",
                )
    except Exception as e:
        log.debug(f"GitHub search error: {e}")
    return None


async def do_basic_research(member_info) -> list[ResearchResult]:
    results: list[ResearchResult] = []
    try:
        email = member_info.email
        name = member_info.name

        if email and not is_personal_email(email):
            domain = email.split("@")[1]
            company_info = await get_company_info(domain)
            if company_info:
                results.append(company_info)

            if name:
                github_info = await get_github_info(name)
                if github_info:
                    results.append(github_info)
    except Exception as e:
        log.error(f"Research error: {e}")

    return results
