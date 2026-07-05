"""
Centralized API response helpers.

Provides consistent response structures for all API endpoints.
"""

from typing import Any, Dict, List, Optional
from fastapi import status
from pydantic import BaseModel


class ResponseMeta(BaseModel):
    """Response metadata for pagination and filters."""
    page: Optional[int] = None
    page_size: Optional[int] = None
    total_pages: Optional[int] = None
    total: Optional[int] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: Any = None
    meta: Optional[Dict[str, Any]] = None


class ErrorDetail(BaseModel):
    """Error detail information."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    errors: List[ErrorDetail] = []


def success_response(
    data: Any = None,
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_200_OK,
) -> Dict[str, Any]:
    """
    Create a standardized success response.

    Args:
        data: Response data
        message: Success message
        meta: Metadata (pagination info, etc.)
        status_code: HTTP status code

    Returns:
        Standardized success response dictionary
    """
    response = {
        "success": True,
        "message": message,
        "data": data,
        "meta": meta,
    }
    return response


def error_response(
    message: str,
    errors: Optional[List[Dict[str, Any]]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        message: Error message
        errors: List of error details
        status_code: HTTP status code

    Returns:
        Standardized error response dictionary
    """
    error_details = []
    if errors:
        for error in errors:
            if isinstance(error, dict):
                error_details.append(ErrorDetail(**error))
            else:
                error_details.append(error)

    response = {
        "success": False,
        "message": message,
        "errors": error_details,
    }
    return response


def pagination_meta(
    page: int,
    page_size: int,
    total: int,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create pagination metadata.

    Args:
        page: Current page number
        page_size: Items per page
        total: Total number of items
        sort_by: Field being sorted by
        sort_order: Sort direction (asc/desc)
        filters: Applied filters

    Returns:
        Pagination metadata dictionary
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    meta = {
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total": total,
    }

    if sort_by:
        meta["sort_by"] = sort_by
        meta["sort_order"] = sort_order

    if filters:
        meta["filters"] = filters

    return meta
