"""Helpers to build the standard success/paginated response envelopes."""

from typing import Any


def success(data: Any) -> dict:
    return {"success": True, "data": data}


def paginated(items: Any, *, page: int, page_size: int, total: int) -> dict:
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return {
        "success": True,
        "data": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }
