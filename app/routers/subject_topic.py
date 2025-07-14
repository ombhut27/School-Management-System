from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from sqlalchemy.exc import IntegrityError
from app.auth2 import get_current_user
from typing import List
from sqlalchemy import select

router = APIRouter()

@router.post("/api/add_subject_topic", response_model=schemas.SubjectTopicOut, status_code=status.HTTP_201_CREATED)
def add_subject_topic(
    subject_topic: schemas.SubjectTopicCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Role check - only admin can add subject topics
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admin and teacher users can create subject topics")
    
    # Validate subject exists
    subject = db.query(models.Subject).filter(models.Subject.id == subject_topic.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail=f"Subject with id '{subject_topic.subject_id}' not found")
    
    # Validate board exists
    board = db.query(models.Board).filter(models.Board.id == subject_topic.board_id).first()
    if not board:
        raise HTTPException(status_code=404, detail=f"Board with id '{subject_topic.board_id}' not found")
    
    # Validate grade exists
    grade = db.query(models.Grade).filter(models.Grade.id == subject_topic.grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail=f"Grade with id '{subject_topic.grade_id}' not found")
    
    # Validate that the subject is actually assigned to this grade through divisions
    division_subject = db.query(models.DivisionSubject).join(
        models.Division, models.DivisionSubject.division_id == models.Division.id
    ).filter(
        models.DivisionSubject.subject_id == subject_topic.subject_id,
        models.Division.grade_id == subject_topic.grade_id
    ).first()
    
    if not division_subject:
        raise HTTPException(
            status_code=400, 
            detail=f"Subject with id '{subject_topic.subject_id}' is not assigned to grade '{subject_topic.grade_id}'. Please assign the subject to a division of this grade first."
        )
    
    new_subject_topic = models.SubjectTopic(**subject_topic.model_dump())
    try:
        db.add(new_subject_topic)
        db.commit()
        db.refresh(new_subject_topic)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A subject topic with these details already exists.")
    
    # Get related names for response
    return {
        "id": new_subject_topic.id,
        "topic": new_subject_topic.topic,
        "sub_topic": new_subject_topic.sub_topic,
        "subject_id": new_subject_topic.subject_id,
        "board_id": new_subject_topic.board_id,
        "grade_id": new_subject_topic.grade_id,
        "subject_name": subject.name,
        "board_name": board.name,
        "grade_name": grade.name,
        "created_at": new_subject_topic.created_at,
        "updated_at": new_subject_topic.updated_at
    }

@router.get("/api/get_subject_topics", response_model=List[schemas.SubjectTopicOut])
def get_subject_topics(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Role check - only admin can view subject topics
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in ["admin" , "teacher"]:
        raise HTTPException(status_code=403, detail="Only admin users can view subject topics")
    
    subject_topics = db.query(models.SubjectTopic).all()
    result = []
    
    for topic in subject_topics:
        # Get related names
        subject = db.query(models.Subject).filter(models.Subject.id == topic.subject_id).first()
        board = db.query(models.Board).filter(models.Board.id == topic.board_id).first()
        grade = db.query(models.Grade).filter(models.Grade.id == topic.grade_id).first()
        
        result.append({
            "id": topic.id,
            "topic": topic.topic,
            "sub_topic": topic.sub_topic,
            "subject_id": topic.subject_id,
            "board_id": topic.board_id,
            "grade_id": topic.grade_id,
            "subject_name": subject.name if subject else None,
            "board_name": board.name if board else None,
            "grade_name": grade.name if grade else None,
            "created_at": topic.created_at,
            "updated_at": topic.updated_at
        })
    
    return result 