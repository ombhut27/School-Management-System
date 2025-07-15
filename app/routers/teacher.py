from fastapi import APIRouter
from app.database import get_db
from app import models, schemas
from fastapi import Depends, HTTPException, status
from app.auth2 import get_current_user
from sqlalchemy.orm import Session
from app.models import TeacherDivision, Subject
from sqlalchemy import select

router = APIRouter()


@router.post("/api/add_teacher_details", response_model=schemas.TeacherOut, status_code=201)
async def create_teacher(
    create_teacher: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    # Allow access if the user is teacher
    if not role or role.name.lower() not in ["teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check for existing teacher with the same email
    existing_teacher = db.query(models.Teacher).filter(models.Teacher.email == create_teacher.email).first()
    if existing_teacher:
        raise HTTPException(status_code=400, detail="A teacher with this email already exists.")
    
    # Find school by id
    school = db.query(models.School).filter(models.School.id == create_teacher.school_id).first()
    if not school:
        raise HTTPException(
            status_code=404, 
            detail=f"School with id '{create_teacher.school_id}' not found"
        )
    
    # Check if teacher profile already exists for this user
    teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
    if teacher:
        raise HTTPException(
            status_code=403,
            detail="profile already exists"
        )

    # Prepare data for the new teacher
    teacher_data = create_teacher.model_dump()
    teacher_data.pop('school_id')  
    new_teacher = models.Teacher(school_id=school.id, user_id=current_user.id, **teacher_data)
    
    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)
    
    # Get school name for response
    school = db.query(models.School).filter(models.School.id == new_teacher.school_id).first()
    
    return {
        "id": new_teacher.id,
        "full_name": f"{new_teacher.first_name} {new_teacher.last_name}",
        "email": new_teacher.email,
        "created_at": new_teacher.created_at,
        "updated_at": new_teacher.updated_at,
        "school_id": new_teacher.school_id,
        "school_name": school.name if school else None
    }

@router.get("/api/get_teachers", response_model=list[schemas.TeacherOut])
def get_teachers(db: Session = Depends(get_db)):
    teachers = db.query(
        models.Teacher,
        models.School
    ).join(models.School, models.Teacher.school_id == models.School.id).all()
    result = []
    for teacher, school in teachers:
        result.append({
            "id": teacher.id,
            "full_name": f"{teacher.first_name} {teacher.last_name}",
            "email": teacher.email,
            "created_at": teacher.created_at,
            "updated_at": teacher.updated_at,
            "school_id": teacher.school_id,
            "school_name": school.name if school else None
        })
    return result

@router.patch("/api/update_teacher/{teacher_id}", response_model=schemas.TeacherOut)
def update_teacher(
    teacher_id: int,
    teacher_update: schemas.TeacherUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check permissions - only teacher can update their own details
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in ["teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the teacher to update (only if owned by current user)
    db_teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id, models.Teacher.user_id == current_user.id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or not owned by user")
    
    # Update only the provided fields
    update_data = teacher_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_teacher, field, value)
    
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

@router.put("/api/update_teacher/{teacher_id}", response_model=schemas.TeacherOut)
def put_teacher(
    teacher_id: int,
    teacher_update: schemas.TeacherCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check permissions - only teacher can update their own details
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get the teacher to update (only if owned by current user)
    db_teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_id, models.Teacher.user_id == current_user.id).first()
    if not db_teacher:
        raise HTTPException(status_code=404, detail="Teacher not found or not owned by user")
    
    # Replace all fields with the new data
    teacher_data = teacher_update.model_dump()
    for field, value in teacher_data.items():
        setattr(db_teacher, field, value)
    
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

@router.post("/api/add_teacher_division", response_model=dict)
async def add_teacher_division(
    teacher_division: schemas.AddTeacherDivision,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    # Allow access if the user is admin only
    if not role or role.name.lower() not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admin users can assign teachers to divisions")
    
    # Check if division exists
    division = db.query(models.Division).filter(models.Division.id == teacher_division.division_id).first()
    if not division:
        raise HTTPException(
            status_code=404,
            detail=f"Division with id '{teacher_division.division_id}' not found"
        )
    
    # Check if subject exists
    subject = db.query(models.Subject).filter(models.Subject.id == teacher_division.subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=404,
            detail=f"Subject with id '{teacher_division.subject_id}' not found"
        )
    
    # Check if subject is assigned to the division
    division_subject = db.query(models.DivisionSubject).filter(
        models.DivisionSubject.division_id == teacher_division.division_id,
        models.DivisionSubject.subject_id == teacher_division.subject_id
    ).first()
    if not division_subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with id '{teacher_division.subject_id}' is not assigned to division '{teacher_division.division_id}'"
        )
    
    # Check if teacher exists
    teacher = db.query(models.Teacher).filter(models.Teacher.id == teacher_division.teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=404,
            detail=f"Teacher with id '{teacher_division.teacher_id}' not found"
        )
    
    # Create new teacher division  entry
    new_teacher_division = models.TeacherDivision(**teacher_division.model_dump())
    
    try:
        db.add(new_teacher_division)
        db.commit()
        db.refresh(new_teacher_division)
    except Exception as e:
        db.rollback()  
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while saving the teacher division: {str(e)}"
        )
    
    # grade and section names 
    division_info = db.query(
        models.Division,
        models.Grade,
        models.Section
    ).join(
        models.Grade, models.Division.grade_id == models.Grade.id
    ).join(
        models.Section, models.Division.section_id == models.Section.id
    ).filter(
        models.Division.id == division.id
    ).first()
    division_name = ""
    if division_info:
        _, grade, section = division_info
        division_name = f"{grade.name or ''} {section.name or ''}"
    return {
        "division_name": division_name,
        "subject_name": subject.name,
        "teacher_name": teacher.first_name + " " + teacher.last_name
    }

@router.get("/api/teacher/me/subjects", response_model=list[schemas.SubjectOut])
def get_my_subjects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    subjects = db.query(Subject).join(TeacherDivision, Subject.id == TeacherDivision.subject_id)\
        .filter(TeacherDivision.teacher_id == teacher.id).distinct().all()
    return subjects

