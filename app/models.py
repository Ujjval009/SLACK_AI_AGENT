import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func

from app.database import Base


class MemberAnalysis(Base):
    __tablename__ = "member_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    member_id = Column(String(255), nullable=True, index=True)
    member_name = Column(String(255), nullable=False)
    member_email = Column(String(255), nullable=True)
    member_title = Column(String(255), nullable=True)
    member_timezone = Column(String(100), nullable=True)
    fit_score = Column(Integer, nullable=False)
    insights = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    research_data = Column(JSON, nullable=True)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_to_slack = Column(Boolean, default=False)
    sent_to_slack_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<MemberAnalysis(id={self.id}, name={self.member_name}, fit_score={self.fit_score})>"
