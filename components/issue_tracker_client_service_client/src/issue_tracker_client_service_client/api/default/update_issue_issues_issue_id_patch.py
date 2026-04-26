from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.issue_out import IssueOut
from ...models.update_issue_in import UpdateIssueIn
from ...types import UNSET, Response, Unset


def _get_kwargs(
    issue_id: str,
    *,
    body: UpdateIssueIn,
    session_id: None | str | Unset = UNSET,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    cookies = {}
    if session_id is not UNSET:
        cookies["session_id"] = session_id

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": "/issues/{issue_id}".format(
            issue_id=quote(str(issue_id), safe=""),
        ),
        "cookies": cookies,
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | IssueOut | None:
    if response.status_code == 200:
        response_200 = IssueOut.from_dict(response.json())

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
) -> Response[HTTPValidationError | IssueOut]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    issue_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateIssueIn,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | IssueOut]:
    """Update Issue

     Update an issue using the shared API contract.

    Args:
        issue_id (str):
        session_id (None | str | Unset):
        body (UpdateIssueIn): Represent a request to update an issue in the shared API shape.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | IssueOut]
    """

    kwargs = _get_kwargs(
        issue_id=issue_id,
        body=body,
        session_id=session_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    issue_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateIssueIn,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | IssueOut | None:
    """Update Issue

     Update an issue using the shared API contract.

    Args:
        issue_id (str):
        session_id (None | str | Unset):
        body (UpdateIssueIn): Represent a request to update an issue in the shared API shape.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | IssueOut
    """

    return sync_detailed(
        issue_id=issue_id,
        client=client,
        body=body,
        session_id=session_id,
    ).parsed


async def asyncio_detailed(
    issue_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateIssueIn,
    session_id: None | str | Unset = UNSET,
) -> Response[HTTPValidationError | IssueOut]:
    """Update Issue

     Update an issue using the shared API contract.

    Args:
        issue_id (str):
        session_id (None | str | Unset):
        body (UpdateIssueIn): Represent a request to update an issue in the shared API shape.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[HTTPValidationError | IssueOut]
    """

    kwargs = _get_kwargs(
        issue_id=issue_id,
        body=body,
        session_id=session_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    issue_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: UpdateIssueIn,
    session_id: None | str | Unset = UNSET,
) -> HTTPValidationError | IssueOut | None:
    """Update Issue

     Update an issue using the shared API contract.

    Args:
        issue_id (str):
        session_id (None | str | Unset):
        body (UpdateIssueIn): Represent a request to update an issue in the shared API shape.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        HTTPValidationError | IssueOut
    """

    return (
        await asyncio_detailed(
            issue_id=issue_id,
            client=client,
            body=body,
            session_id=session_id,
        )
    ).parsed
