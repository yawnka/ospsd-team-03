"""Pydantic schemas for AI chat requests and responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AIChatIn(BaseModel):
    """Incoming AI chat request."""

    message: str = Field(..., min_length=1)


class AIActionOut(BaseModel):
    """A tool/action performed by the AI workflow."""

    tool: str
    detail: str | None = None


class AIChatOut(BaseModel):
    """Outgoing AI chat response."""

    reply: str
    actions: list[AIActionOut] = Field(default_factory=list)
