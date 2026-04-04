# Issue Tracker Service Client (Auto-Generated)

A client library for accessing Issue Tracker Client Service

## Usage
The generated client provides a type-safe interface for calling the service.

In this project, authentication is handled via a session cookie (`session_id`), not via bearer tokens or `Authorization` headers.

The adapter layer is responsible for configuring the client so authenticated requests include this cookie. Consumers of the client should not manually manage authentication.

```python
from issue_tracker_client_service_client import Client

client = Client(base_url="https://api.example.com")
```

Now call your endpoint and use your models:

```python
from issue_tracker_client_service_client.models import MyDataModel
from issue_tracker_client_service_client.api.my_tag import get_my_data_model
from issue_tracker_client_service_client.types import Response

with client as client:
    my_data: MyDataModel = get_my_data_model.sync(client=client)
    # or if you need more info (e.g. status_code)
    response: Response[MyDataModel] = get_my_data_model.sync_detailed(client=client)
```

Or do the same thing with an async version:

```python
from issue_tracker_client_service_client.models import MyDataModel
from issue_tracker_client_service_client.api.my_tag import get_my_data_model
from issue_tracker_client_service_client.types import Response

async with client as client:
    my_data: MyDataModel = await get_my_data_model.asyncio(client=client)
    response: Response[MyDataModel] = await get_my_data_model.asyncio_detailed(client=client)
```

By default, when you're calling an HTTPS API it will attempt to verify that SSL is working correctly. Using certificate verification is highly recommended most of the time, but sometimes you may need to authenticate to a server (especially an internal server) using a custom certificate bundle.

```python
client = Client(
    base_url="https://internal_api.example.com",
    verify_ssl="/path/to/certificate_bundle.pem",
)
```

You can also disable certificate validation altogether, but beware that **this is a security risk**.

```python
client = Client(
    base_url="https://internal_api.example.com",
    verify_ssl=False
)
```

Things to know:
1. Every path/method combo becomes a Python module with four functions:
    1. `sync`: Blocking request that returns parsed data (if successful) or `None`
    1. `sync_detailed`: Blocking request that always returns a `Request`, optionally with `parsed` set if the request was successful.
    1. `asyncio`: Like `sync` but async instead of blocking
    1. `asyncio_detailed`: Like `sync_detailed` but async instead of blocking

1. All path/query params, and bodies become method arguments.
1. If your endpoint had any tags on it, the first tag will be used as a module name for the function (my_tag above)
1. Any endpoint which did not have a tag will be in `issue_tracker_client_service_client.api.default`

## Advanced customizations

There are more settings on the generated `Client` class which let you control more runtime behavior, check out the docstring on that class for more info. You can also customize the underlying `httpx.Client` or `httpx.AsyncClient` (depending on your use-case):

```python
from issue_tracker_client_service_client import Client

def log_request(request):
    print(f"Request event hook: {request.method} {request.url} - Waiting for response")

def log_response(response):
    request = response.request
    print(f"Response event hook: {request.method} {request.url} - Status {response.status_code}")

client = Client(
    base_url="https://api.example.com",
    httpx_args={"event_hooks": {"request": [log_request], "response": [log_response]}},
)

# Or get the underlying httpx client to modify directly with client.get_httpx_client() or client.get_async_httpx_client()
```

You can even set the httpx client directly, but beware that this will override any existing settings (e.g., base_url):

```python
import httpx
from issue_tracker_client_service_client import Client

client = Client(
    base_url="https://api.example.com",
)
# Note that base_url needs to be re-set, as would any shared cookies, headers, etc.
client.set_httpx_client(httpx.Client(base_url="https://api.example.com", proxies="http://localhost:8030"))
```

## Building / publishing this package
This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies and packaging. Here are the basics:
1. Update the metadata in `pyproject.toml` (e.g. version)
1. Build a wheel: `uv build`
1. Publish to PyPI: `uv publish`

If you want to install this client into another project without publishing it (e.g. for development) then:
1. If that project **is using uv workspaces**, add it as a workspace dependency in the root `pyproject.toml` under `[tool.uv.sources]`
1. Otherwise, install directly: `uv add <path-to-this-client>`
