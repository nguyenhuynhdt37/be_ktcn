from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Query parameters for generic pagination requests.
    """

    page: int = Field(default=1, ge=1, description="Page index (1-based)")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items per page")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Enveloped paginated response schema.
    """

    items: list[T]
    total: int
    page: int
    pageSize: int
    totalPages: int

    @classmethod
    def create(
        cls, items: list[T], total: int, params: PaginationParams
    ) -> "PaginatedResponse[T]":
        """
        Creates a PaginatedResponse helper from a list, a total,
        and pagination parameters.
        """
        pages = (total + params.limit - 1) // params.limit if params.limit > 0 else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            pageSize=params.limit,
            totalPages=pages,
        )
