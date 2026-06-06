import json
import re
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from app.config import settings
from app.logger import log
from app.schemas import MemberInfo, ResearchResult, AnalysisResult


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.3,
    api_key=settings.groq_api_key,
)


def _build_research_summary(research_data: list[ResearchResult]) -> str:
    if not research_data:
        return "Limited research data available"
    return "\n".join(f"{r.title}: {r.content}" for r in research_data)


async def analyze_with_ai(
    member_info: MemberInfo,
    research_data: list[ResearchResult],
) -> AnalysisResult:
    prompt = ChatPromptTemplate.from_template(
        """Analyze this new community member for fit with our commercial product.

Company: {company}
Product: {product}

Member:
- Name: {name}
- Email: {email}
- Title: {title}

Research Data:
{research}

Provide a JSON response with:
- fitScore (0-100): likelihood they'd be interested in our product
- insights: array of 3-5 key observations
- recommendations: array of 2-4 engagement suggestions

Consider job title, company size, technical background, and budget authority."""
    )

    try:
        research_summary = _build_research_summary(research_data)
        chain = prompt | llm
        result = await chain.ainvoke({
            "company": settings.company_name,
            "product": settings.company_product,
            "name": member_info.name,
            "email": member_info.email or "Not provided",
            "title": member_info.title or "Not provided",
            "research": research_summary,
        })

        response_text = result.content if hasattr(result, "content") else str(result)
        cleaned = re.sub(r"```json\n?|```", "", response_text).strip()
        analysis = json.loads(cleaned)

        return AnalysisResult(
            fitScore=max(0, min(100, analysis.get("fitScore", 50))),
            insights=(
                analysis["insights"]
                if isinstance(analysis.get("insights"), list)
                else ["Analysis completed"]
            ),
            recommendations=(
                analysis["recommendations"]
                if isinstance(analysis.get("recommendations"), list)
                else ["Follow up recommended"]
            ),
        )

    except Exception as e:
        log.error(f"AI analysis error: {e}")
        return AnalysisResult(
            fitScore=50,
            insights=["Unable to complete full analysis"],
            recommendations=["Manual review recommended"],
        )
