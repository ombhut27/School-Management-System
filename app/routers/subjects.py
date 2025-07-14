from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth2 import get_current_user
from typing import List
from sqlalchemy import select

router = APIRouter()

@router.post("/api/add_subject", response_model=schemas.SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject: schemas.SubjectCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    # Allow access if the user is teacher
    if not role or role.name.lower() != "admin":
      raise HTTPException(status_code=403, detail="Only admin users are allowed to add subject details")

    # Check for existing subject with the same name or code
    existing_subject = db.query(models.Subject).filter(
        (models.Subject.name == subject.name) |
        (models.Subject.code == subject.code)
    ).first()
    if existing_subject:
        raise HTTPException(status_code=400, detail="A subject with this name or code already exists.")
    
    db_subject = models.Subject(**subject.model_dump())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@router.get("/api/get_subjects", response_model=List[schemas.SubjectOut])
def get_subjects(db: Session = Depends(get_db)):
    subjects = db.query(models.Subject).all()
    return subjects


    



