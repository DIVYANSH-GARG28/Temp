from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

class UserRole(str, Enum):
    STUDENT = "student"
    ALUMNI = "alumni"
    FACULTY = "faculty"
    RECRUITER = "recruiter"
    FOUNDER = "founder"
    ADMIN = "admin"

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured diagnostics or validation errors")

class StandardErrorResponse(BaseModel):
    error: ErrorDetail

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    limit: int
    offset: int
