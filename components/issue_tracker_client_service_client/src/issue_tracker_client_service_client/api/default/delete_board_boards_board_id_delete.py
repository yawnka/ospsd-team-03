from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.success_out import SuccessOut
from ...types import UNSET, Response, Unset


def _get_kwargs(
    board_id: str,
    *,
    session_id: None | str | Unset = UNSET,
) -> dict[str, Any]:

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id

    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": "/boards/{board_id}".format(
            board_id=quote(str(board_id), safe=""),
        ),
        "cookies": cookies,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | SuccessOut | None:
    if response.status_code == 200:
        response_200 = SuccessOut.from_dict(response.json())

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
) -> Response[HTTPValidationError | SuccessOut]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | SuccessOut]:
    """Delete Board

     Delete a board using the shared API contract.

    Args:
        board_id (str):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SuccessOut]
    """

    kwargs = _get_kwargs(
        board_id=board_id,
        session_id=session_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | SuccessOut | None:
    """Delete Board

     Delete a board using the shared API contract.

    Args:
        board_id (str):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SuccessOut
    """

    return sync_detailed(
        board_id=board_id,
        client=client,
        session_id=session_id,
    ).parsed


async def asyncio_detailed(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | SuccessOut]:
    """Delete Board

     Delete a board using the shared API contract.

    Args:
        board_id (str):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | SuccessOut]
    """

    kwargs = _get_kwargs(
        board_id=board_id,
        session_id=session_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | SuccessOut | None:
    """Delete Board

     Delete a board using the shared API contract.

    Args:
        board_id (str):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | SuccessOut
    """

    return (
        await asyncio_detailed(
            board_id=board_id,
            client=client,
            session_id=session_id,
        )
    ).parsed
