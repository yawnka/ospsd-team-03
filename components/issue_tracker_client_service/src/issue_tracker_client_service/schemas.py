"""Pydantic schemas for request and response bodies."""

from typing import Literal

from pydantic import BaseModel


class HealthOut(BaseModel):
    """Represent the health check response."""

    status: str


class BoardOut(BaseModel):
    """Represent a serialized board in the shared API shape."""

    id: str
    board_name: str


class IssueOut(BaseModel):
    """Represent a serialized issue in the shared API shape."""

    id: str
    title: str
    desc: str
    members: list[str] | None
    due_date: str | None
    status: str
    board_id: str


class CreateBoardIn(BaseModel):
    """Represent a request to create a board."""

    name: str


class UpdateBoardIn(BaseModel):
    """Represent a request to update a board."""

    name: str | None = None


class CreateIssueIn(BaseModel):
    """Represent a request to create an issue in the shared API shape."""

    title: str
    desc: str | None = None
    members: list[str] | None = None
    due_date: str | None = None
    status: Literal["to_do", "in_progress", "completed"] = "to_do"


class UpdateIssueIn(BaseModel):
    """Represent a request to update an issue in the shared API shape."""

    title: str | None = None
    desc: str | None = None
    members: list[str] | None = None
    due_date: str | None = None
    status: Literal["to_do", "in_progress", "completed"] | None = None
    board_id: str | None = None


class SuccessOut(BaseModel):
    """Represent a simple success response body."""

    success: bool


class LegacyIssueOut(BaseModel):
    """Represent a serialized issue in the legacy HW2 shape."""

    id: int
    title: str
    body: str
    state: str


class LegacyCreateIssueIn(BaseModel):
    """Represent a request to create an issue in the legacy HW2 shape."""

    title: str
    body: str


class CommentOut(BaseModel):
    """Represent a serialized comment."""

    id: int
    body: str


class AddCommentIn(BaseModel):
    """Represent a request to add a comment."""

    body: str


class AuthStatusOut(BaseModel):
    """Represent a successful auth response."""

    status: str
    session_id: str | None = None


class TokenIn(BaseModel):
    """Represent the token POST body sent by the callback JS bridge."""

    token: str
    state: str | None = None
