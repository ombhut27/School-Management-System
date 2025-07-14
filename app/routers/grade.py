from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from sqlalchemy.exc import IntegrityError
from app.auth2 import get_current_user
from typing import List
from sqlalchemy import select

router = APIRouter()

@router.post("/api/add_grade", response_model=schemas.GradeOut, status_code=status.HTTP_201_CREATED)
def add_grade(
    grade: schemas.GradeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Only admin can add grade (optional: add role check)
    new_grade = models.Grade(**grade.model_dump())
    try:
        db.add(new_grade)
        db.commit()
        db.refresh(new_grade)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A grade with this name already exists.")
    return new_grade

@router.get("/api/get_grades", response_model=List[schemas.GradeOut])
def get_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()
