from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from sqlalchemy.exc import IntegrityError
from app.auth2 import get_current_user
from typing import List

router = APIRouter()

@router.post("/api/add_section", response_model=schemas.SectionOut, status_code=status.HTTP_201_CREATED)
def add_section(
    section: schemas.SectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Only admin can add section
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    new_section = models.Section(**section.model_dump())
    try:
        db.add(new_section)
        db.commit()
        db.refresh(new_section)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A section with this name already exists.")
    return new_section

@router.get("/api/get_sections", response_model=List[schemas.SectionOut])
def get_sections(db: Session = Depends(get_db)):
    return db.query(models.Section).all()
