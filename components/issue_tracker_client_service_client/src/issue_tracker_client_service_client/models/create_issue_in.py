from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.status import Status
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateIssueIn")


@_attrs_define
class CreateIssueIn:
    """Represent a request to create an issue in the shared API shape.

    Attributes:
        title (str):
        desc (None | str | Unset):
        members (list[str] | None | Unset):
        due_date (None | str | Unset):
        status (Status | Unset): Status values for an issue.
    """

    title: str
    desc: None | str | Unset = UNSET
    members: list[str] | None | Unset = UNSET
    due_date: None | str | Unset = UNSET
    status: Status | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        title = self.title

        desc: None | str | Unset
        if isinstance(self.desc, Unset):
            desc = UNSET
        else:
            desc = self.desc

        members: list[str] | None | Unset
        if isinstance(self.members, Unset):
            members = UNSET
        elif isinstance(self.members, list):
            members = self.members

        else:
            members = self.members

        due_date: None | str | Unset
        if isinstance(self.due_date, Unset):
            due_date = UNSET
        else:
            due_date = self.due_date

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "title": title,
            }
        )
        if desc is not UNSET:
            field_dict["desc"] = desc
        if members is not UNSET:
            field_dict["members"] = members
        if due_date is not UNSET:
            field_dict["due_date"] = due_date
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        title = d.pop("title")

        def _parse_desc(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        desc = _parse_desc(d.pop("desc", UNSET))

        def _parse_members(data: object) -> list[str] | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, list):
                    raise TypeError()
                members_type_0 = cast(list[str], data)

                return members_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(list[str] | None | Unset, data)

        members = _parse_members(d.pop("members", UNSET))

        def _parse_due_date(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        due_date = _parse_due_date(d.pop("due_date", UNSET))

        _status = d.pop("status", UNSET)
        status: Status | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = Status(_status)

        create_issue_in = cls(
            title=title,
            desc=desc,
            members=members,
            due_date=due_date,
            status=status,
        )

        create_issue_in.additional_properties = d
        return create_issue_in

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
