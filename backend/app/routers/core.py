from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.core import Company, Branch, User, Role
from app.schemas.core import (
    CompanyCreate, CompanyOut,
    BranchCreate, BranchOut,
    UserOut,
    RoleCreate, RoleOut,
)

router = APIRouter(tags=["core"])


# ---- Companies ----

@router.get("/companies", response_model=List[CompanyOut])
async def list_companies(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Company))
    return result.scalars().all()


@router.post("/companies", response_model=CompanyOut, status_code=201)
async def create_company(
    payload: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = Company(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/companies/{company_id}", response_model=CompanyOut)
async def get_company(
    company_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(select(Company).where(Company.id == company_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Company not found")
    return obj


# ---- Branches ----

@router.get("/branches", response_model=List[BranchOut])
async def list_branches(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Branch))
    return result.scalars().all()


@router.post("/branches", response_model=BranchOut, status_code=201)
async def create_branch(
    payload: BranchCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = Branch(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/branches/{branch_id}", response_model=BranchOut)
async def get_branch(
    branch_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Branch not found")
    return obj


# ---- Roles ----

@router.get("/roles", response_model=List[RoleOut])
async def list_roles(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Role))
    return result.scalars().all()


@router.post("/roles", response_model=RoleOut, status_code=201)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = Role(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ---- Users ----

@router.get("/users", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="User not found")
    return obj
