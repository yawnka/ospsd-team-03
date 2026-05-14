from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.board_out import BoardOut
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    session_id: None | str | Unset = UNSET,
) -> dict[str, Any]:

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/boards",
        "cookies": cookies,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | list[BoardOut] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = BoardOut.from_dict(response_200_item_data)

            response_200.append(response_200_item)

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
) -> Response[HTTPValidationError | list[BoardOut]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[BoardOut]]:
    """Get Boards

     List boards using the shared API contract.

    Args:
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[BoardOut]]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | list[BoardOut] | None:
    """Get Boards

     List boards using the shared API contract.

    Args:
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[BoardOut]
    """

    return sync_detailed(
        client=client,
        session_id=session_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | list[BoardOut]]:
    """Get Boards

     List boards using the shared API contract.

    Args:
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[BoardOut]]
    """

    kwargs = _get_kwargs(
        session_id=session_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | list[BoardOut] | None:
    """Get Boards

     List boards using the shared API contract.

    Args:
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[BoardOut]
    """

    return (
        await asyncio_detailed(
            client=client,
            session_id=session_id,
        )
    ).parsed
