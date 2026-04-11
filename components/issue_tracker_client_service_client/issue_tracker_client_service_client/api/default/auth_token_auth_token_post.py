from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_status_out import AuthStatusOut
from ...models.http_validation_error import HTTPValidationError
from ...models.token_in import TokenIn
from ...types import Response


def _get_kwargs(
    *,
    body: TokenIn,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/auth/token",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthStatusOut | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AuthStatusOut.from_dict(response.json())

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
) -> Response[AuthStatusOut | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TokenIn,
) -> Response[AuthStatusOut | HTTPValidationError]:
    """Auth Token

     Receive the Trello token posted by the callback page's JS bridge.

    This endpoint is called automatically by the JavaScript returned from
    ``/auth/callback`` — it is not intended to be invoked directly.

    Args:
        body (TokenIn): Represent the token POST body sent by the callback JS bridge.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthStatusOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: TokenIn,
) -> AuthStatusOut | HTTPValidationError | None:
    """Auth Token

     Receive the Trello token posted by the callback page's JS bridge.

    This endpoint is called automatically by the JavaScript returned from
    ``/auth/callback`` — it is not intended to be invoked directly.

    Args:
        body (TokenIn): Represent the token POST body sent by the callback JS bridge.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthStatusOut | HTTPValidationError
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: TokenIn,
) -> Response[AuthStatusOut | HTTPValidationError]:
    """Auth Token

     Receive the Trello token posted by the callback page's JS bridge.

    This endpoint is called automatically by the JavaScript returned from
    ``/auth/callback`` — it is not intended to be invoked directly.

    Args:
        body (TokenIn): Represent the token POST body sent by the callback JS bridge.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[AuthStatusOut | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: TokenIn,
) -> AuthStatusOut | HTTPValidationError | None:
    """Auth Token

     Receive the Trello token posted by the callback page's JS bridge.

    This endpoint is called automatically by the JavaScript returned from
    ``/auth/callback`` — it is not intended to be invoked directly.

    Args:
        body (TokenIn): Represent the token POST body sent by the callback JS bridge.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        AuthStatusOut | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
