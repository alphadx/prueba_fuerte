from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr


# ---- Company ----

class CompanyBase(BaseModel):
    name: str
    rut: str
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyOut(CompanyBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Branch ----

class BranchBase(BaseModel):
    company_id: int
    name: str
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class BranchCreate(BranchBase):
    pass


class BranchOut(BranchBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Role ----

class RoleBase(BaseModel):
    name: str
    permissions: Optional[Any] = None


class RoleCreate(RoleBase):
    pass


class RoleOut(RoleBase):
    id: int

    model_config = {"from_attributes": True}


# ---- User ----

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    branch_id: Optional[int] = None
    role_id: Optional[int] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Token ----

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None


# ---- AuditLog ----

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    table_name: str
    record_id: Optional[int]
    old_values: Optional[Any]
    new_values: Optional[Any]
    created_at: datetime

    model_config = {"from_attributes": True}
