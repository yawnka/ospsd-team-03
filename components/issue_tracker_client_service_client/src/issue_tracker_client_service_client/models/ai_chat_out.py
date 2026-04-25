from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.ai_action_out import AIActionOut


T = TypeVar("T", bound="AIChatOut")


@_attrs_define
class AIChatOut:
    """Outgoing AI chat response.

    Attributes:
        reply (str):
        actions (list[AIActionOut] | Unset):
    """

    reply: str
    actions: list[AIActionOut] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        reply = self.reply

        actions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.actions, Unset):
            actions = []
            for actions_item_data in self.actions:
                actions_item = actions_item_data.to_dict()
                actions.append(actions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "reply": reply,
            }
        )
        if actions is not UNSET:
            field_dict["actions"] = actions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.ai_action_out import AIActionOut

        d = dict(src_dict)
        reply = d.pop("reply")

        _actions = d.pop("actions", UNSET)
        actions: list[AIActionOut] | Unset = UNSET
        if _actions is not UNSET:
            actions = []
            for actions_item_data in _actions:
                actions_item = AIActionOut.from_dict(actions_item_data)

                actions.append(actions_item)

        ai_chat_out = cls(
            reply=reply,
            actions=actions,
        )

        ai_chat_out.additional_properties = d
        return ai_chat_out

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
