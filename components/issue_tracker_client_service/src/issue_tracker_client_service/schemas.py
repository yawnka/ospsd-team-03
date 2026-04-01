"""Pydantic schemas for request and response bodies."""

from pydantic import BaseModel


class HealthOut(BaseModel):
    """Represent the health check response."""

    status: str


class IssueOut(BaseModel):
    """Represent a serialized issue."""

    id: int
    title: str
    body: str
    state: str


class CommentOut(BaseModel):
    """Represent a serialized comment."""

    id: int
    body: str


class CreateIssueIn(BaseModel):
    """Represent a request to create an issue."""

    title: str
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
