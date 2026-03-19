from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.http_validation_error import HTTPValidationError
from ...models.issue_out import IssueOut
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    board: str,
    *,
    session_id: None | str | Unset = UNSET,

) -> dict[str, Any]:
    

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id



    

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/boards/{board}/issues".format(board=quote(str(board), safe=""),),
        "cookies": cookies,
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> HTTPValidationError | list[IssueOut] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in (_response_200):
            response_200_item = IssueOut.from_dict(response_200_item_data)



            response_200.append(response_200_item)

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[HTTPValidationError | list[IssueOut]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    board: str,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,

) -> Response[HTTPValidationError | list[IssueOut]]:
    """ List Issues

     List issues for a board.

    Args:
        board (str):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[IssueOut]]
     """


    kwargs = _get_kwargs(
        board=board,
session_id=session_id,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    board: str,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,

) -> HTTPValidationError | list[IssueOut] | None:
    """ List Issues

     List issues for a board.

    Args:
        board (str):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[IssueOut]
     """


    return sync_detailed(
        board=board,
client=client,
session_id=session_id,

    ).parsed

async def asyncio_detailed(
    board: str,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,

) -> Response[HTTPValidationError | list[IssueOut]]:
    """ List Issues

     List issues for a board.

    Args:
        board (str):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | list[IssueOut]]
     """


    kwargs = _get_kwargs(
        board=board,
session_id=session_id,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    board: str,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,

) -> HTTPValidationError | list[IssueOut] | None:
    """ List Issues

     List issues for a board.

    Args:
        board (str):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | list[IssueOut]
     """


    return (await asyncio_detailed(
        board=board,
client=client,
session_id=session_id,

    )).parsed
