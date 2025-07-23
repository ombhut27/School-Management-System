from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth2 import get_current_user

router = APIRouter()

@router.post("/api/add_student_details", response_model=schemas.StudentOut, status_code=201)
def create_student(
    student: schemas.StudentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Role check (allow only students)
    allowed_roles = ["student"]
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in allowed_roles:
        raise HTTPException(status_code=403, detail="Must be a student")

    # School validation
    school = db.query(models.School).filter(models.School.id == student.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail=f"School with id '{student.school_id}' not found")

    # Division validation (by grade_id, section_id, and school)
    division = db.query(models.Division).filter(
        models.Division.grade_id == student.grade_id,
        models.Division.section_id == student.section_id,
        models.Division.school_id == school.id
    ).first()
    if not division:
        raise HTTPException(status_code=404, detail=f"Division for school id '{student.school_id}', grade_id '{student.grade_id}', section_id '{student.section_id}' not found")

    # Prepare student data
    student_data = student.model_dump(exclude={"grade_id", "section_id"})
    db_student = models.Student(user_id=current_user.id, **student_data)

    try:
        db.add(db_student)
        db.flush()
        # Create student_division entry
        student_division = models.StudentDivision(
            student_id=db_student.id,
            division_id=division.id,
            is_current=True
        )
        db.add(student_division)
        # Assign all subjects of the division to the student
        all_division_subjects = db.query(models.DivisionSubject).filter(models.DivisionSubject.division_id == division.id).all()
        student_subject_rels = [
            models.StudentSubjectRel(
                student_id=db_student.id,
                subject_id=div_sub.subject_id,
                division_id=division.id,
                is_active=True
            )
            for div_sub in all_division_subjects
        ]
        db.add_all(student_subject_rels)
        db.commit()
        db.refresh(db_student)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error occurred during student creation: {str(e)}")

    # Get grade and section names
    grade = db.query(models.Grade).filter(models.Grade.id == division.grade_id).first()
    section = db.query(models.Section).filter(models.Section.id == division.section_id).first()

    # Return student and division details
    return {
        "id": db_student.id,
        "display_name": f"{db_student.first_name} {db_student.last_name}",
        "email": db_student.email,
        "created_at": db_student.created_at,
        "updated_at": db_student.updated_at,
        "school_id": db_student.school_id,
        "school_name": school.name,
        "division_id": division.id if division else None,
        "grade_id": division.grade_id if division else None,
        "section_id": division.section_id if division else None,
        "grade_name": grade.name if grade else None,
        "section_name": section.name if section else None,
    }

@router.get("/api/get_students", response_model=list[schemas.StudentOut])
def get_students(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Allow only admin and teacher
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admin and teacher users can view students")

    students = db.query(
        models.Student,
        models.School,
        models.StudentDivision,
        models.Division,
        models.Grade,
        models.Section
    ).join(
        models.School, models.Student.school_id == models.School.id
    ).outerjoin(
        models.StudentDivision, (models.StudentDivision.student_id == models.Student.id) & (models.StudentDivision.is_current == True)
    ).outerjoin(
        models.Division, models.StudentDivision.division_id == models.Division.id
    ).outerjoin(
        models.Grade, models.Division.grade_id == models.Grade.id
    ).outerjoin(
        models.Section, models.Division.section_id == models.Section.id
    ).all()

    result = []
    for student, school, division, grade, section in students:
        result.append({
            "id": student.id,
            "display_name": f"{student.first_name} {student.last_name}",
            "email": student.email,
            "created_at": student.created_at,
            "updated_at": student.updated_at,
            "school_id": student.school_id,
            "school_name": school.name if school else None,
            "division_id": division.id if division else None,
            "grade_id": grade.id if grade else None,
            "section_id": section.id if section else None,
            "grade_name": grade.name if grade else None,
            "section_name": section.name if section else None
        })
    return result

@router.patch("/api/update_student/{student_id}", response_model=schemas.StudentOut)
def update_student(
    student_id: int,
    student_update: schemas.StudentUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    # Allow access if the user is student
    if not role or role.name.lower() != "student":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # Get the student record
    db_student = db.query(models.Student).filter(models.Student.id == student_id, models.Student.user_id == current_user.id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found or not owned by user")
    # Update fields if provided
    update_data = student_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    # If grade_id or section_id or school_id changed, update StudentDivision
    if "grade_id" in update_data or "section_id" in update_data or "school_id" in update_data:
        grade_id = update_data.get("grade_id", db_student.grade_id)
        section_id = update_data.get("section_id", db_student.section_id)
        school_id = update_data.get("school_id", db_student.school_id)
        division = db.query(models.Division).filter(
            models.Division.grade_id == grade_id,
            models.Division.section_id == section_id,
            models.Division.school_id == school_id
        ).first()
        if not division:
            raise HTTPException(status_code=404, detail="Division not found for the given grade and section")
        # Set all previous student_divisions to not current
        db.query(models.StudentDivision).filter(
            models.StudentDivision.student_id == db_student.id,
            models.StudentDivision.is_current == True
        ).update({"is_current": False})
        # Add new student_division
        student_division = models.StudentDivision(
            student_id=db_student.id,
            division_id=division.id,
            is_current=True
        )
        db.add(student_division)
        db.commit()
    # Get grade and section names
    student_division = db.query(models.StudentDivision).filter(models.StudentDivision.student_id == db_student.id, models.StudentDivision.is_current == True).first()
    division = db.query(models.Division).filter(models.Division.id == student_division.division_id).first() if student_division else None
    grade = db.query(models.Grade).filter(models.Grade.id == division.grade_id).first() if division else None
    section = db.query(models.Section).filter(models.Section.id == division.section_id).first() if division else None
    return {
        **db_student.__dict__,
        "division_id": division.id if division else None,
        "grade_id": division.grade_id if division else None,
        "section_id": division.section_id if division else None,
        "grade_name": grade.name if grade else None,
        "section_name": section.name if section else None,
    }

@router.post("/api/add_subject_to_student", response_model=schemas.AddSubjectsOut, status_code=201)
def add_subject_to_student(
    payload: schemas.AddSubjects,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    # Allow access if the user is admin or student (case-insensitive)
    if not role or role.name.lower() not in ["admin", "student"]:
        raise HTTPException(status_code=403, detail="Only admin or student users can add subjects to a student.")
    # Check if student exists
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check if subject exists
    subject = db.query(models.Subject).filter(models.Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Check if subject already assigned to student
    existing_rel = db.query(models.StudentSubjectRel).filter(
        models.StudentSubjectRel.student_id == payload.student_id,
        models.StudentSubjectRel.subject_id == payload.subject_id,
        models.StudentSubjectRel.is_active == True
    ).first()
    if existing_rel:
        raise HTTPException(status_code=400, detail="Subject already assigned to student")

    # Find current division for student
    student_division = db.query(models.StudentDivision).filter(
        models.StudentDivision.student_id == payload.student_id,
        models.StudentDivision.is_current == True
    ).first()
    division_id = student_division.division_id if student_division else None

    # Assign subject to student
    new_rel = models.StudentSubjectRel(
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        division_id=division_id,
        is_active=True
    )
    db.add(new_rel)
    db.commit()

    return schemas.AddSubjectsOut(
        student_name=f"{student.first_name} {student.last_name}",
        subject_name=str(subject.name)
    )

