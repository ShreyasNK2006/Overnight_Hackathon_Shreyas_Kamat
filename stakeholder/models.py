"""
Role Management Data Models
Pydantic models for role-based document routing
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class RoleBase(BaseModel):
    """Base role information"""
    role_name: str = Field(..., min_length=1, max_length=255, description="Name of the role")
    department: Optional[str] = Field(None, max_length=255, description="Department name")
    responsibilities: str = Field(
        ..., 
        min_length=20, 
        description="Detailed description of responsibilities (min 20 chars for good matching)"
    )
    priority: int = Field(1, ge=1, le=10, description="Priority level (1-10, higher = more important)")
    business_id: Optional[UUID] = Field(None, description="Business/tenant ID for multi-tenant support")


class RoleCreate(RoleBase):
    """Model for creating a new role"""
    pass


class RoleUpdate(BaseModel):
    """Model for updating role (all fields optional)"""
    role_name: Optional[str] = Field(None, min_length=1, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    responsibilities: Optional[str] = Field(None, min_length=20)
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None


class Role(RoleBase):
    """Complete role model with database fields"""
    id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoleMatch(BaseModel):
    """Model for role routing results"""
    role_id: UUID
    role_name: str
    department: Optional[str]
    responsibilities: str
    priority: int
    similarity: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    confidence: str = Field(..., description="Confidence level: high, medium, low")

    class Config:
        from_attributes = True


class DocumentRoutingRequest(BaseModel):
    """Request model for document routing"""
    document_summary: str = Field(
        ..., 
        min_length=10, 
        description="Summary or content of the document to route"
    )
    business_id: Optional[UUID] = Field(None, description="Filter by business ID")
    top_k: int = Field(3, ge=1, le=10, description="Number of matches to return")
    threshold: float = Field(0.6, ge=0.0, le=1.0, description="Minimum similarity threshold")


class DocumentRoutingResponse(BaseModel):
    """Response model for document routing"""
    matches: list[RoleMatch] = Field(..., description="Matched roles ranked by relevance")
    best_match: Optional[RoleMatch] = Field(None, description="Primary recipient role")
    fallback_used: bool = Field(False, description="Whether fallback to manager was used")
    processing_time_ms: float = Field(..., description="Time taken to process routing")


class RoleStats(BaseModel):
    """Statistics about roles in the system"""
    total_roles: int
    active_roles: int
    inactive_roles: int
    departments: list[str]
    roles_list: list[str]
