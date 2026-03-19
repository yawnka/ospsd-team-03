from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.add_comment_in import AddCommentIn
from ...models.comment_out import CommentOut
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    board: str,
    issue_id: int,
    *,
    body: AddCommentIn,
    session_id: None | str | Unset = UNSET,

) -> dict[str, Any]:
    headers: dict[str, Any] = {}


    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id



    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/boards/{board}/issues/{issue_id}/comments".format(board=quote(str(board), safe=""),issue_id=quote(str(issue_id), safe=""),),
        "cookies": cookies,
    }

    _kwargs["json"] = body.to_dict()


    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> CommentOut | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CommentOut.from_dict(response.json())



        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[CommentOut | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    board: str,
    issue_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: AddCommentIn,
    session_id: None | str | Unset = UNSET,

) -> Response[CommentOut | HTTPValidationError]:
    """ Add Comment

     Add a comment to an issue.

    Args:
        board (str):
        issue_id (int):
        session_id (None | str | Unset):
        body (AddCommentIn): Represent a request to add a comment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CommentOut | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        board=board,
issue_id=issue_id,
body=body,
session_id=session_id,

    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)

def sync(
    board: str,
    issue_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: AddCommentIn,
    session_id: None | str | Unset = UNSET,

) -> CommentOut | HTTPValidationError | None:
    """ Add Comment

     Add a comment to an issue.

    Args:
        board (str):
        issue_id (int):
        session_id (None | str | Unset):
        body (AddCommentIn): Represent a request to add a comment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CommentOut | HTTPValidationError
     """


    return sync_detailed(
        board=board,
issue_id=issue_id,
client=client,
body=body,
session_id=session_id,

    ).parsed

async def asyncio_detailed(
    board: str,
    issue_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: AddCommentIn,
    session_id: None | str | Unset = UNSET,

) -> Response[CommentOut | HTTPValidationError]:
    """ Add Comment

     Add a comment to an issue.

    Args:
        board (str):
        issue_id (int):
        session_id (None | str | Unset):
        body (AddCommentIn): Represent a request to add a comment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CommentOut | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        board=board,
issue_id=issue_id,
body=body,
session_id=session_id,

    )

    response = await client.get_async_httpx_client().request(
        **kwargs
    )

    return _build_response(client=client, response=response)

async def asyncio(
    board: str,
    issue_id: int,
    *,
    client: AuthenticatedClient | Client,
    body: AddCommentIn,
    session_id: None | str | Unset = UNSET,

) -> CommentOut | HTTPValidationError | None:
    """ Add Comment

     Add a comment to an issue.

    Args:
        board (str):
        issue_id (int):
        session_id (None | str | Unset):
        body (AddCommentIn): Represent a request to add a comment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CommentOut | HTTPValidationError
     """


    return (await asyncio_detailed(
        board=board,
issue_id=issue_id,
client=client,
body=body,
session_id=session_id,

    )).parsed
