from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth2 import get_current_user
from typing import List
from sqlalchemy import select

router = APIRouter()

@router.post("/api/add_division_details", response_model=schemas.DivisionOut, status_code=status.HTTP_201_CREATED)
def create_division(
    division: schemas.DivisionCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    # Allow access if the user is admin
    if not role or role.name.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin users are allowed to add division details")

    # Check for existing division with same details
    existing = db.query(models.Division).filter(
        models.Division.grade_id == division.grade_id,
        models.Division.section_id == division.section_id,
        models.Division.academic_year == division.academic_year,
        models.Division.school_id == division.school_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Division already exists for this grade, section, academic year, and school.")

    db_division = models.Division(**division.model_dump())
    db.add(db_division)
    db.commit()
    db.refresh(db_division)
    return db_division

@router.get("/api/get_divisions", response_model=List[schemas.DivisionOutWithNames])
def get_divisions(db: Session = Depends(get_db)):
    divisions = db.query(
        models.Division,
        models.Grade,
        models.Section,
        models.School
    ).join(
        models.Grade, models.Division.grade_id == models.Grade.id
    ).join(
        models.Section, models.Division.section_id == models.Section.id
    ).join(
        models.School, models.Division.school_id == models.School.id
    ).all()
    result = []
    for division, grade, section, school in divisions:
        result.append({
            "id": division.id,
            "grade_id": division.grade_id,
            "section_id": division.section_id,
            "school_id": division.school_id,
            "grade_name": grade.name if grade else None,
            "section_name": section.name if section else None,
            "school_name": school.name if school else None,
            "academic_year": division.academic_year,
            "created_at": division.created_at,
            "updated_at": division.updated_at
        })
    return result

@router.post("/api/assign_division_subject", response_model=list[schemas.DivisionSubjectOut], status_code=status.HTTP_201_CREATED)
def assign_division_subject(
    payload: schemas.DivisionSubjectBulkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Enforce admin-only access
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can assign division subjects")

    # Get division and school
    division = db.query(models.Division).filter(models.Division.id == payload.division_id).first()
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")
    school_id = division.school_id

    # Check for duplicates in payload
    subject_ids = list(payload.subjects.values())
    if len(subject_ids) != len(set(subject_ids)):
        raise HTTPException(status_code=400, detail="Duplicate subject IDs in payload.")

    # Find already assigned subjects
    existing = db.query(models.DivisionSubject.subject_id).filter(
        models.DivisionSubject.division_id == payload.division_id,
        models.DivisionSubject.school_id == school_id,
        models.DivisionSubject.subject_id.in_(subject_ids)
    ).all()
    existing_ids = {row[0] for row in existing}

    # Prepare new assignments
    new_subjects = [
        models.DivisionSubject(
            school_id=school_id,
            division_id=payload.division_id,
            subject_id=sid
        )
        for _, sid in payload.subjects.items()
        if sid not in existing_ids
    ]

    if not new_subjects:
        raise HTTPException(status_code=400, detail="All subjects already assigned to this division.")

    db.bulk_save_objects(new_subjects)
    db.commit()

    # Return all assignments for this division
    assigned = db.query(models.DivisionSubject).filter(
        models.DivisionSubject.division_id == payload.division_id
    ).all()
    return assigned

@router.get("/api/get_division_subjects", response_model=List[schemas.DivisionSubjectOut])
def get_division_subjects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Enforce admin-only access
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can view division-subject assignments")

    division_subjects = db.query(models.DivisionSubject).all()
    return division_subjects