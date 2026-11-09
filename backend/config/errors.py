"""Shared error type for business-rule failures, and the DRF handler that turns them into 400s."""

from rest_framework.response import Response
from rest_framework.views import exception_handler


class DomainError(Exception):
    """A rule was broken (e.g. 'group is full'). The message is safe to show to the member."""


def api_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response({"detail": str(exc)}, status=400)
    return exception_handler(exc, context)
