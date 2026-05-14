"""Pydantic schemas for request and response bodies."""

from api.issue import Status as SharedStatus  # type: ignore[import-untyped]
from pydantic import BaseModel, field_validator

ISO_DATE_LENGTH = 10
YEAR_MONTH_SEPARATOR_INDEX = 4
MONTH_DAY_SEPARATOR_INDEX = 7

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
    status: SharedStatus
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
    description: str | None = None
    members: list[str] | None = None
    due_date: str | None = None
    status: SharedStatus = SharedStatus.TO_DO

    @field_validator("description", mode="before")
    @classmethod
    def blank_out_default_description(cls, value: object) -> object:
        """Ignore Swagger placeholder descriptions."""
        if value in (None, "", "string"):
            return None
        return value

    @field_validator("members", mode="before")
    @classmethod
    def blank_out_default_members(cls, value: object) -> object:
        """Ignore Swagger placeholder member IDs."""
        if value in (None, [], ["string"]):
            return None
        return value

    @field_validator("due_date", mode="before")
    @classmethod
    def normalize_due_date(cls, value: object) -> object:
        """Normalize due date values before sending them to Trello."""
        if value in (None, "", "string"):
            return None

        text = str(value).strip()

        if (
            len(text) == ISO_DATE_LENGTH
            and text[YEAR_MONTH_SEPARATOR_INDEX] == "-"
            and text[MONTH_DAY_SEPARATOR_INDEX] == "-"
        ):
            return f"{text}T00:00:00.000Z"

        return text

    @field_validator("status", mode="before")
    @classmethod
    def default_invalid_status(cls, value: object) -> SharedStatus:
        """Ignore Swagger placeholder status."""
        if value in (None, "", "string"):
            return SharedStatus.TO_DO

        if isinstance(value, SharedStatus):
            return value

        normalized = str(value).lower().strip().replace(" ", "_").replace("-", "_")

        try:
            return SharedStatus(normalized)
        except ValueError:
            return SharedStatus.TO_DO

class UpdateIssueIn(BaseModel):
    """Represent a request to update an issue in the shared API shape."""

    title: str | None = None
    desc: str | None = None
    members: list[str] | None = None
    due_date: str | None = None
    status: SharedStatus | None = None
    board_id: str | None = None

    @field_validator("board_id", mode="before")
    @classmethod
    def blank_out_default_board_id(cls, value: object) -> object:
        """Ignore Swagger placeholder board ID."""
        if value in (None, "", "string"):
            return None
        return value

    @field_validator("desc", mode="before")
    @classmethod
    def blank_out_default_desc(cls, value: object) -> object:
        """Ignore Swagger placeholder descriptions."""
        if value in (None, "", "string"):
            return None
        return value

    @field_validator("members", mode="before")
    @classmethod
    def blank_out_default_members(cls, value: object) -> object:
        """Ignore Swagger placeholder member IDs."""
        if value in (None, [], ["string"]):
            return None
        return value

    @field_validator("due_date", mode="before")
    @classmethod
    def normalize_due_date(cls, value: object) -> object:
        """Normalize due date values before sending them to Trello."""
        if value in (None, "", "string"):
            return None

        text = str(value).strip()

        if (
            len(text) == ISO_DATE_LENGTH
            and text[YEAR_MONTH_SEPARATOR_INDEX] == "-"
            and text[MONTH_DAY_SEPARATOR_INDEX] == "-"
        ):
            return f"{text}T00:00:00.000Z"

        return text

    @field_validator("status", mode="before")
    @classmethod
    def normalize_update_status(cls, value: object) -> SharedStatus | None:
        """Normalize update status values before enum validation."""
        if value in (None, "", "string"):
            return None

        if isinstance(value, SharedStatus):
            return value

        normalized = str(value).lower().strip().replace(" ", "_").replace("-", "_")

        try:
            return SharedStatus(normalized)
        except ValueError:
            return None


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
