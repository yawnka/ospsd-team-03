"""Chat provider registration for the shared chat vertical."""

import os
from importlib import import_module

CHAT_CLIENT_IMPL_MODULE_ENV = "CHAT_CLIENT_IMPL_MODULE"
DEFAULT_CHAT_CLIENT_IMPL_MODULE = "discord_client_impl"


def register_chat_client() -> None:
    """Register the configured chat-client implementation.

    The implementation module should register itself with chat_client_api
    when imported, following the HW1 get_client() pattern.
    """
    module_name = os.getenv(
        CHAT_CLIENT_IMPL_MODULE_ENV,
        DEFAULT_CHAT_CLIENT_IMPL_MODULE,
    )
    import_module(module_name)
