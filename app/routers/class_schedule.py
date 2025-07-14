from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.auth2 import get_current_user
from typing import List, Optional
from datetime import datetime, date

router = APIRouter()

@router.post("/api/add_class_schedule", response_model=schemas.ClassScheduleOut, status_code=status.HTTP_201_CREATED)
def create_class_schedule(
    class_schedule: schemas.ClassScheduleCreate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    # Allow access if the user is admin 
    if not role or role.name.lower() not in ["admin"]:
        raise HTTPException(status_code=403, detail="Only admin is allowed to add class schedules")

    # Validate that subject exists
    subject = db.query(models.Subject).filter(models.Subject.id == class_schedule.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Validate that division exists
    division = db.query(models.Division).filter(models.Division.id == class_schedule.division_id).first()
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")

    # Validate that teacher exists
    teacher = db.query(models.Teacher).filter(models.Teacher.id == class_schedule.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Validate teacher-division-subject association
    teacher_division_subject = db.query(models.TeacherDivision).filter(
        models.TeacherDivision.teacher_id == class_schedule.teacher_id,
        models.TeacherDivision.division_id == class_schedule.division_id,
        models.TeacherDivision.subject_id == class_schedule.subject_id
    ).first()
    
    if not teacher_division_subject:
        raise HTTPException(
            status_code=400, 
            detail="Teacher is not assigned to teach this subject in this division"
        )

    # Validate division-subject association
    division_subject = db.query(models.DivisionSubject).filter(
        models.DivisionSubject.division_id == class_schedule.division_id,
        models.DivisionSubject.subject_id == class_schedule.subject_id
    ).first()
    
    if not division_subject:
        raise HTTPException(
            status_code=400, 
            detail="Subject is not assigned to this division"
        )

    # Parse date and times
    try:
        schedule_date = date.today() if not class_schedule.date else datetime.strptime(class_schedule.date, "%Y-%m-%d").date()
        start_time = class_schedule.start_time
        end_time = class_schedule.end_time
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date/time format: {str(e)}")


    # Check for teacher time conflicts (allow back-to-back classes)
    teacher_conflict = db.query(models.ClassSchedule).filter(
        models.ClassSchedule.teacher_id == class_schedule.teacher_id,
        models.ClassSchedule.date == schedule_date,
        models.ClassSchedule.start_time < end_time,
        models.ClassSchedule.end_time > start_time
    ).first()
    if teacher_conflict:
        raise HTTPException(status_code=400, detail="Teacher is already assigned to another class at this time")

    # Create the class schedule
    db_class_schedule = models.ClassSchedule(
        period=class_schedule.period,
        date=schedule_date,
        subject_id=class_schedule.subject_id,
        division_id=class_schedule.division_id,
        teacher_id=class_schedule.teacher_id,
        start_time=start_time,
        end_time=end_time
    )
    
    db.add(db_class_schedule)
    db.commit()
    db.refresh(db_class_schedule)
    
    # Get related data for response
    subject_name = subject.name
    teacher_name = f"{teacher.first_name} {teacher.last_name}"
    
    # Create response with additional data
    response_data = {
        "id": db_class_schedule.id,
        "period": db_class_schedule.period,
        "date": db_class_schedule.date.isoformat(),
        "subject_id": db_class_schedule.subject_id,
        "division_id": db_class_schedule.division_id,
        "teacher_id": db_class_schedule.teacher_id,
        "start_time": db_class_schedule.start_time.isoformat(),
        "end_time": db_class_schedule.end_time.isoformat(),
        "created_at": db_class_schedule.created_at,
        "updated_at": db_class_schedule.updated_at,
        "subject_name": subject_name,
        "division_name": f"Grade {division.grade_id} Section {division.section_id}",
        "teacher_name": teacher_name
    }
    
    return response_data

@router.get("/api/get_class_schedules", response_model=List[schemas.ClassScheduleOut])
def get_class_schedules(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Role check - only admin and teacher can view class schedules
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admin and teacher users can view class schedules")
    
    class_schedules = db.query(models.ClassSchedule).all()
    result = []
    
    for schedule in class_schedules:
        # Get related names
        subject = db.query(models.Subject).filter(models.Subject.id == schedule.subject_id).first()
        teacher = db.query(models.Teacher).filter(models.Teacher.id == schedule.teacher_id).first()
        division = db.query(models.Division).filter(models.Division.id == schedule.division_id).first()
        
        result.append({
            "id": schedule.id,
            "period": schedule.period,
            "date": schedule.date.isoformat(),
            "subject_id": schedule.subject_id,
            "division_id": schedule.division_id,
            "teacher_id": schedule.teacher_id,
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat(),
            "subject_name": subject.name if subject else None,
            "division_name": f"Grade {division.grade_id} Section {division.section_id}" if division else None,
            "teacher_name": f"{teacher.first_name} {teacher.last_name}" if teacher else None,
            "created_at": schedule.created_at,
            "updated_at": schedule.updated_at
        })
    
    return result

@router.get("/api/teacher_class_schedule", response_model=List[schemas.ClassScheduleOut])
def get_teacher_class_schedule(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Find the teacher profile for the current user
    teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")

    # Get all class schedules for this teacher
    class_schedules = db.query(models.ClassSchedule).filter(models.ClassSchedule.teacher_id == teacher.id).all()

    result = []
    for schedule in class_schedules:
        subject = db.query(models.Subject).filter(models.Subject.id == schedule.subject_id).first()
        division = db.query(models.Division).filter(models.Division.id == schedule.division_id).first()
        teacher_name = f"{teacher.first_name} {teacher.last_name}"
        result.append({
            "id": schedule.id,
            "period": schedule.period,
            "date": schedule.date.isoformat(),
            "subject_id": schedule.subject_id,
            "division_id": schedule.division_id,
            "teacher_id": schedule.teacher_id,
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat(),
            "created_at": schedule.created_at,
            "updated_at": schedule.updated_at,
            "subject_name": subject.name if subject else None,
            "division_name": f"Grade {division.grade_id} Section {division.section_id}" if division else None,
            "teacher_name": teacher_name
        })
    return result

@router.post("/api/set_class_topic", status_code=status.HTTP_201_CREATED, response_model=schemas.SetClassTopicOut)
async def set_class_topic(
    class_topic: schemas.SetClassTopic, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Get the user's role relationship from the database
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    
    # Allow access if the user is Teacher, Administrator, or ssai
    allowed_roles = ["teacher"]
    if not role or role.name not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be a Teacher to set class topics"
        )
    
    # Validate that class schedule exists
    class_schedule = db.query(models.ClassSchedule).filter(models.ClassSchedule.id == class_topic.class_schedule_id).first()
    if not class_schedule:
        raise HTTPException(status_code=404, detail="Class schedule not found")
    
    # Validate that subject topic exists
    subject_topic = db.query(models.SubjectTopic).filter(models.SubjectTopic.id == class_topic.subject_topic_id).first()
    if not subject_topic:
        raise HTTPException(status_code=404, detail="Subject topic not found")
    
    # Ensure subject_id matches between class schedule and subject topic
    if class_schedule.subject_id != subject_topic.subject_id: # type: ignore
        raise HTTPException(
            status_code=400,
            detail="Subject of class schedule and subject topic do not match"
        )

    # Check if the topic is already assigned to this class schedule
    existing_topic = db.query(models.ClassDetailsRel).filter(
        models.ClassDetailsRel.class_schedule_id == class_topic.class_schedule_id,
        models.ClassDetailsRel.subject_topic_id == class_topic.subject_topic_id
    ).first()
    
    if existing_topic:
        raise HTTPException(
            status_code=400, 
            detail="This topic is already assigned to this class schedule"
        )
    
    # Create the class topic relationship
    new_class_topic = models.ClassDetailsRel(
        class_schedule_id=class_topic.class_schedule_id,
        subject_topic_id=class_topic.subject_topic_id
    )
    
    db.add(new_class_topic)
    db.commit()
    db.refresh(new_class_topic)
    
    # Get related data for detailed response
    subject = db.query(models.Subject).filter(models.Subject.id == class_schedule.subject_id).first()
    teacher = db.query(models.Teacher).filter(models.Teacher.id == class_schedule.teacher_id).first()
    division = db.query(models.Division).filter(models.Division.id == class_schedule.division_id).first()
    grade = db.query(models.Grade).filter(models.Grade.id == subject_topic.grade_id).first()
    board = db.query(models.Board).filter(models.Board.id == subject_topic.board_id).first()
    
    # Create detailed response
    response_data = {
        "id": new_class_topic.id,
        "class_schedule_id": new_class_topic.class_schedule_id,
        "subject_topic_id": new_class_topic.subject_topic_id,
        "class_schedule_details": {
            "period": class_schedule.period,
            "date": class_schedule.date.isoformat(),
            "start_time": class_schedule.start_time.isoformat(),
            "end_time": class_schedule.end_time.isoformat(),
            "subject_name": subject.name if subject else None,
            "teacher_name": f"{teacher.first_name} {teacher.last_name}" if teacher else None,
            "division_name": f"Grade {division.grade_id} Section {division.section_id}" if division else None
        },
        "subject_topic_details": {
            "topic": subject_topic.topic,
            "sub_topic": subject_topic.sub_topic,
            "subject_name": subject.name if subject else None,
            "grade_name": grade.name if grade else None,
            "board_name": board.name if board else None
        }
    }
    
    return response_data

@router.get("/api/student_class_schedule", response_model=List[schemas.ClassScheduleOut])
def get_student_class_schedule(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Find the student profile for the current user
    student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # Find the student's current division
    student_division = db.query(models.StudentDivision).filter(
        models.StudentDivision.student_id == student.id,
        models.StudentDivision.is_current == True
    ).first()
    if not student_division:
        raise HTTPException(status_code=404, detail="Current division for student not found")

    # Get all class schedules for this division
    class_schedules = db.query(models.ClassSchedule).filter(models.ClassSchedule.division_id == student_division.division_id).all()

    result = []
    for schedule in class_schedules:
        subject = db.query(models.Subject).filter(models.Subject.id == schedule.subject_id).first()
        division = db.query(models.Division).filter(models.Division.id == schedule.division_id).first()
        teacher = db.query(models.Teacher).filter(models.Teacher.id == schedule.teacher_id).first()
        teacher_name = f"{teacher.first_name} {teacher.last_name}" if teacher else None
        result.append({
            "id": schedule.id,
            "period": schedule.period,
            "date": schedule.date.isoformat(),
            "subject_id": schedule.subject_id,
            "division_id": schedule.division_id,
            "teacher_id": schedule.teacher_id,
            "start_time": schedule.start_time.isoformat(),
            "end_time": schedule.end_time.isoformat(),
            "created_at": schedule.created_at,
            "updated_at": schedule.updated_at,
            "subject_name": subject.name if subject else None,
            "division_name": f"Grade {division.grade_id} Section {division.section_id}" if division else None,
            "teacher_name": teacher_name
        })
    return result

@router.get("/api/current_student_class")
async def get_current_student_class(
    date_str: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    student = db.query(models.Student).filter(models.Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    student_division = db.query(models.StudentDivision).filter(
        models.StudentDivision.student_id == student.id,
        models.StudentDivision.is_current == True
    ).first()
    if not student_division:
        raise HTTPException(status_code=404, detail="Current division for student not found")

    try:
        if date_str:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            query_date = date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    current_time = datetime.now().time()

    class_details = db.query(
        models.ClassSchedule,
        models.School.name.label('school_name'),
        models.School.id.label('school_id'),
        models.Division.id.label('division_id'),
        models.Division.grade_id.label('grade_id'),
        models.Division.section_id.label('section_id'),
        models.Grade.name.label('grade_name'),
        models.Section.name.label('section_name'),
        models.Subject.name.label('subject_name'),
        models.Subject.id.label('subject_id'),
        models.Teacher.id.label('teacher_id'),
        (models.Teacher.first_name + ' ' + models.Teacher.last_name).label('teacher_name')
    ).join(
        models.Division, models.ClassSchedule.division_id == models.Division.id
    ).join(
        models.School, models.Division.school_id == models.School.id
    ).join(
        models.Grade, models.Division.grade_id == models.Grade.id
    ).join(
        models.Section, models.Division.section_id == models.Section.id
    ).join(
        models.Subject, models.ClassSchedule.subject_id == models.Subject.id
    ).join(
        models.Teacher, models.ClassSchedule.teacher_id == models.Teacher.id
    ).filter(
        models.ClassSchedule.division_id == student_division.division_id,
        models.ClassSchedule.date == query_date,
        models.ClassSchedule.start_time <= current_time,
        models.ClassSchedule.end_time >= current_time
    ).order_by(models.ClassSchedule.start_time).first()

    if not class_details:
        raise HTTPException(status_code=404, detail="No Current Class found")

    class_schedule = class_details[0]

    details = db.query(
        models.ClassDetailsRel,
        models.SubjectTopic.topic,
        models.SubjectTopic.sub_topic
    ).join(
        models.SubjectTopic, models.SubjectTopic.id == models.ClassDetailsRel.subject_topic_id
    ).filter(
        models.ClassDetailsRel.class_schedule_id == class_schedule.id
    ).all()

    topics_dict = {}
    for rel in details:
        topic_name = rel.topic
        subtopic_name = rel.sub_topic
        if topic_name not in topics_dict:
            topics_dict[topic_name] = []
        if subtopic_name:
            topics_dict[topic_name].append(subtopic_name)
    detail_list = [
        {"topic": topic, "sub_topic": subtopics}
        for topic, subtopics in topics_dict.items()
    ]

    return {
        "class_schedule_id": class_schedule.id,
        "date": class_schedule.date,
        "period": class_schedule.period,
        "start_time": class_schedule.start_time,
        "end_time": class_schedule.end_time,
        "school_name": class_details.school_name,
        "division_id": class_details.division_id,
        "grade_id": class_details.grade_id,
        "grade_name": class_details.grade_name,
        "section_id": class_details.section_id,
        "section_name": class_details.section_name,
        "subject_name": class_details.subject_name,
        "teacher_name": class_details.teacher_name,
        "class_details": detail_list,
        "school_id": class_details.school_id,
        "subject_id": class_details.subject_id,
        "teacher_id": class_details.teacher_id
    }

@router.get("/api/current_teacher_class")
async def get_current_teacher_class(
    date_str: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    teacher = db.query(models.Teacher).filter(models.Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")


    try:
        if date_str:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            query_date = date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    
    current_time = datetime.now().time()

    class_details = db.query(
        models.ClassSchedule,
        models.School.name.label('school_name'),
        models.School.id.label('school_id'),
        models.Division.id.label('division_id'),
        models.Division.grade_id.label('grade_id'),
        models.Division.section_id.label('section_id'),
        models.Grade.name.label('grade_name'),
        models.Section.name.label('section_name'),
        models.Subject.name.label('subject_name'),
        models.Subject.id.label('subject_id'),
        models.Teacher.id.label('teacher_id'),
        (models.Teacher.first_name + ' ' + models.Teacher.last_name).label('teacher_name')
    ).join(
        models.Division, models.ClassSchedule.division_id == models.Division.id
    ).join(
        models.School, models.Division.school_id == models.School.id
    ).join(
        models.Grade, models.Division.grade_id == models.Grade.id
    ).join(
        models.Section, models.Division.section_id == models.Section.id
    ).join(
        models.Subject, models.ClassSchedule.subject_id == models.Subject.id
    ).join(
        models.Teacher, models.ClassSchedule.teacher_id == models.Teacher.id
    ).filter(
        models.ClassSchedule.teacher_id == teacher.id,
        models.ClassSchedule.date == query_date,
        models.ClassSchedule.start_time <= current_time,
        models.ClassSchedule.end_time >= current_time
    ).order_by(models.ClassSchedule.start_time).first()

    if not class_details:
        raise HTTPException(status_code=404, detail="No Current Class found")

    class_schedule = class_details[0]

    details = db.query(
        models.ClassDetailsRel,
        models.SubjectTopic.topic,
        models.SubjectTopic.sub_topic
    ).join(
        models.SubjectTopic, models.SubjectTopic.id == models.ClassDetailsRel.subject_topic_id
    ).filter(
        models.ClassDetailsRel.class_schedule_id == class_schedule.id
    ).all()

    topics_dict = {}
    for rel in details:
        topic_name = rel.topic
        subtopic_name = rel.sub_topic
        if topic_name not in topics_dict:
            topics_dict[topic_name] = []
        if subtopic_name:
            topics_dict[topic_name].append(subtopic_name)
    detail_list = [
        {"topic": topic, "sub_topic": subtopics}
        for topic, subtopics in topics_dict.items()
    ]

    return {
        "class_schedule_id": class_schedule.id,
        "date": class_schedule.date,
        "period": class_schedule.period,
        "start_time": class_schedule.start_time,
        "end_time": class_schedule.end_time,
        "school_name": class_details.school_name,
        "school_id": class_details.school_id,
        "division_id": class_details.division_id,
        "grade_id": class_details.grade_id,
        "grade_name": class_details.grade_name,
        "section_id": class_details.section_id,
        "section_name": class_details.section_name,
        "subject_name": class_details.subject_name,
        "teacher_name": class_details.teacher_name,
        "subject_id": class_details.subject_id,
        "teacher_id": class_details.teacher_id,
        "class_details": detail_list
    }
