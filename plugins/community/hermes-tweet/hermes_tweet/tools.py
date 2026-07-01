from __future__ import annotations

from typing import Any, cast

from .catalog import explore as explore_catalog
from .catalog import find_endpoint, normalize_method, normalize_path
from .client import action_enabled, check_api_available, dumps, normalize_query_params, request

ARGS_ERROR = "Tool arguments must be a JSON object."
ACTION_REASON_ERROR = "Action reason is required."


def _args(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return cast("dict[str, Any]", value)


def _args_error() -> str:
    return dumps({"success": False, "error": ARGS_ERROR})


def _text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def explore(args: Any, **_: Any) -> str:
    try:
        tool_args = _args(args)
        if tool_args is None:
            return _args_error()
        return dumps({"success": True, "endpoints": explore_catalog(tool_args)})
    except Exception as exc:
        return dumps({"success": False, "error": str(exc)})


def call_read(args: Any, **_: Any) -> str:
    try:
        tool_args = _args(args)
        if tool_args is None:
            return _args_error()
        path = _text(tool_args.get("path"))
        catalog_path = normalize_path(path)
        endpoint = find_endpoint("GET", catalog_path)
        if endpoint is None:
            return dumps(
                {
                    "success": False,
                    "error": f"Endpoint is not in the Hermes Tweet catalog: GET {path}",
                }
            )
        if endpoint.action:
            return dumps(
                {
                    "success": False,
                    "error": "Use tweet_action for private or write-like endpoints.",
                }
            )
        return dumps(
            request("GET", catalog_path, query=normalize_query_params(tool_args.get("query")))
        )
    except Exception as exc:
        return dumps({"success": False, "error": str(exc)})


def call_action(args: Any, **_: Any) -> str:
    try:
        tool_args = _args(args)
        if tool_args is None:
            return _args_error()
        if not action_enabled():
            return dumps(
                {
                    "success": False,
                    "error": (
                        "tweet_action is disabled. Set HERMES_TWEET_ENABLE_ACTIONS=true "
                        "to enable it."
                    ),
                }
            )
        if not _text(tool_args.get("reason")):
            return dumps({"success": False, "error": ACTION_REASON_ERROR})
        method = normalize_method(tool_args.get("method"), default="POST")
        path = _text(tool_args.get("path"))
        catalog_path = normalize_path(path)
        endpoint = find_endpoint(method, catalog_path)
        if endpoint is None:
            return dumps(
                {
                    "success": False,
                    "error": f"Endpoint is not in the Hermes Tweet catalog: {method} {path}",
                }
            )
        return dumps(
            request(
                method,
                catalog_path,
                query=normalize_query_params(tool_args.get("query")),
                body=tool_args.get("body"),
            )
        )
    except Exception as exc:
        return dumps({"success": False, "error": str(exc)})


def xstatus(raw_args: Any = "") -> str:
    _ = raw_args
    return call_read({"path": "/api/v1/account"})


def xtrends(raw_args: Any = "") -> str:
    category = _text(raw_args)
    query = {"category": category} if category else None
    return call_read({"path": "/api/v1/x/trends", "query": query})


__all__ = [
    "action_enabled",
    "call_action",
    "call_read",
    "check_api_available",
    "explore",
    "xstatus",
    "xtrends",
]
