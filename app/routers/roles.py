from fastapi import APIRouter, Depends, HTTPException, status   
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from pydantic import BaseModel
from sqlalchemy import select

router = APIRouter()

class SimpleMessageResponse(BaseModel):
    success: bool
    message: str

@router.post("/api/create_roles", response_model=schemas.RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(role: schemas.RoleCreate, db: Session = Depends(get_db)):
    # Check if role already exists
    existing_role = db.query(models.UserRole).filter(models.UserRole.name == role.name).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="Role already exists")
    db_role = models.UserRole(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.get("/api/get_roles", response_model=list[schemas.RoleOut])
def get_roles(db: Session = Depends(get_db)):
    roles = db.query(models.UserRole).all()
    return roles
