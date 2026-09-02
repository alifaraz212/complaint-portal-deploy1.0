"""
Custom exception handler for consistent API error responses.

Wraps DRF's default exception handler to provide a uniform error format:
{
    "error": "Human-readable error message",
    "details": { ... }  // optional, field-level errors
}

This makes it easier for frontend developers to handle errors consistently.
"""

from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, dict):
            if "error" not in response.data:
                if "detail" in response.data:
                    response.data = {
                        "error": str(response.data["detail"]),
                    }
                else:
                    response.data = {
                        "error": "Validation failed.",
                        "details": response.data,
                    }
        elif isinstance(response.data, list):
            response.data = {
                "error": response.data[0] if response.data else "An error occurred.",
            }

    return response
