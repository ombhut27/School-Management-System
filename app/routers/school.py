from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth2 import get_current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

router = APIRouter()


@router.post("/api/add_school_details", response_model=schemas.SchoolOut)
def create_school(
    school: schemas.SchoolCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    # Fetch the actual role object
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    # Only allow access if the user is an admin
    if not role or role.name.lower() != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Create the school
    new_school = models.School(**school.model_dump())
    try:
        db.add(new_school)
        db.commit()
        db.refresh(new_school)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A school with this email already exists.")
    return new_school



@router.get("/api/get_schools", response_model=list[schemas.SchoolOut])
def get_schools(db: Session = Depends(get_db)):
    schools = db.query(models.School).all()
    return schools


@router.patch("/api/update_school/{school_id}", response_model=schemas.SchoolOut)
def update_school(
    school_id: int,
    school_update: schemas.SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check permissions - only admin can update schools
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the school to update
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    # Update only the provided fields
    update_data = school_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(school, field, value)
    
    db.commit()
    db.refresh(school)
    return school


@router.put("/api/update_school/{school_id}", response_model=schemas.SchoolOut)
def put_school(
    school_id: int,
    school_update: schemas.SchoolCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check permissions - only admin can update schools
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the school to update
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    
    # Replace all fields with the new data
    school_data = school_update.model_dump()
    for field, value in school_data.items():
        setattr(school, field, value)
    
    db.commit()
    db.refresh(school)
    return school
