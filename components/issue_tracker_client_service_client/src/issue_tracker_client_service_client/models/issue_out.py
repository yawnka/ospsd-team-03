from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.status import Status

T = TypeVar("T", bound="IssueOut")


@_attrs_define
class IssueOut:
    """Represent a serialized issue in the shared API shape.

    Attributes:
        id (str):
        title (str):
        desc (str):
        members (list[str] | None):
        due_date (None | str):
        status (Status): Status values for an issue.
        board_id (str):
    """

    id: str
    title: str
    desc: str
    members: list[str] | None
    due_date: None | str
    status: Status
    board_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        title = self.title

        desc = self.desc

        members: list[str] | None
        if isinstance(self.members, list):
            members = self.members

        else:
            members = self.members

        due_date: None | str
        due_date = self.due_date

        status = self.status.value

        board_id = self.board_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "title": title,
                "desc": desc,
                "members": members,
                "due_date": due_date,
                "status": status,
                "board_id": board_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        title = d.pop("title")

        desc = d.pop("desc")

        def _parse_members(data: object) -> list[str] | None:
            if data is None:
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                members_type_0 = cast(list[str], data)

                return members_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None, data)

        members = _parse_members(d.pop("members"))

        def _parse_due_date(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        due_date = _parse_due_date(d.pop("due_date"))

        status = Status(d.pop("status"))

        board_id = d.pop("board_id")

        issue_out = cls(
            id=id,
            title=title,
            desc=desc,
            members=members,
            due_date=due_date,
            status=status,
            board_id=board_id,
        )

        issue_out.additional_properties = d
        return issue_out

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
