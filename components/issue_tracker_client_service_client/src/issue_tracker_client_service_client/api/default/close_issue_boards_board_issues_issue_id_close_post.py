from http import HTTPStatus
from typing import Any, cast
from urllib.parse import quote

import httpx

from ...client import AuthenticatedClient, Client
from ...types import Response, UNSET
from ... import errors

from ...models.close_issue_boards_board_issues_issue_id_close_post_response_close_issue_boards_board_issues_issue_id_close_post import CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost
from ...models.http_validation_error import HTTPValidationError
from ...types import UNSET, Unset
from typing import cast



def _get_kwargs(
    board: str,
    issue_id: int,
    *,
    session_id: None | str | Unset = UNSET,

) -> dict[str, Any]:
    

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id



    

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/boards/{board}/issues/{issue_id}/close".format(board=quote(str(board), safe=""),issue_id=quote(str(issue_id), safe=""),),
        "cookies": cookies,
    }


    return _kwargs



def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost.from_dict(response.json())



        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())



        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError]:
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
    session_id: None | str | Unset = UNSET,

) -> Response[CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError]:
    """ Close Issue

     Close an existing issue.

    Args:
        board (str):
        issue_id (int):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        board=board,
issue_id=issue_id,
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
    session_id: None | str | Unset = UNSET,

) -> CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError | None:
    """ Close Issue

     Close an existing issue.

    Args:
        board (str):
        issue_id (int):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError
     """


    return sync_detailed(
        board=board,
issue_id=issue_id,
client=client,
session_id=session_id,

    ).parsed

async def asyncio_detailed(
    board: str,
    issue_id: int,
    *,
    client: AuthenticatedClient | Client,
    session_id: None | str | Unset = UNSET,

) -> Response[CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError]:
    """ Close Issue

     Close an existing issue.

    Args:
        board (str):
        issue_id (int):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError]
     """


    kwargs = _get_kwargs(
        board=board,
issue_id=issue_id,
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
    session_id: None | str | Unset = UNSET,

) -> CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError | None:
    """ Close Issue

     Close an existing issue.

    Args:
        board (str):
        issue_id (int):
        session_id (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        CloseIssueBoardsBoardIssuesIssueIdClosePostResponseCloseIssueBoardsBoardIssuesIssueIdClosePost | HTTPValidationError
     """


    return (await asyncio_detailed(
        board=board,
issue_id=issue_id,
client=client,
session_id=session_id,

    )).parsed
