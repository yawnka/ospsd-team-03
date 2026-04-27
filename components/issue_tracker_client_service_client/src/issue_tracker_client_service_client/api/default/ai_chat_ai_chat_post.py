from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.ai_chat_in import AIChatIn
from ...models.ai_chat_out import AIChatOut
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: AIChatIn,
    session_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/ai/chat",
        "cookies": cookies,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AIChatOut | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AIChatOut.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[AIChatOut | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AIChatIn,
    session_id: None | str | Unset = UNSET,
) -> Response[AIChatOut | HTTPValidationError]:
    """Ai Chat

     Handle AI chat requests for the issue tracker.

    Args:
        session_id (None | str | Unset):
        body (AIChatIn): Incoming AI chat request.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AIChatOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        session_id=session_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: AIChatIn,
    session_id: None | str | Unset = UNSET,
) -> AIChatOut | HTTPValidationError | None:
    """Ai Chat

     Handle AI chat requests for the issue tracker.

    Args:
        session_id (None | str | Unset):
        body (AIChatIn): Incoming AI chat request.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AIChatOut | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
        session_id=session_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: AIChatIn,
    session_id: None | str | Unset = UNSET,
) -> Response[AIChatOut | HTTPValidationError]:
    """Ai Chat

     Handle AI chat requests for the issue tracker.

    Args:
        session_id (None | str | Unset):
        body (AIChatIn): Incoming AI chat request.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AIChatOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
        session_id=session_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: AIChatIn,
    session_id: None | str | Unset = UNSET,
) -> AIChatOut | HTTPValidationError | None:
    """Ai Chat

     Handle AI chat requests for the issue tracker.

    Args:
        session_id (None | str | Unset):
        body (AIChatIn): Incoming AI chat request.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AIChatOut | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            session_id=session_id,
        )
    ).parsed
