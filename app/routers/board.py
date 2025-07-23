from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from sqlalchemy.exc import IntegrityError
from app.auth2 import get_current_user
from typing import List

router = APIRouter()

@router.post("/api/add_board", response_model=schemas.BoardOut, status_code=status.HTTP_201_CREATED)
def add_board(
    board: schemas.BoardCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Role check - only admin can add board
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in ["admin"]:
        raise HTTPException(status_code=403, detail="Only admin users can create boards")
    
    new_board = models.Board(**board.model_dump())
    try:
        db.add(new_board)
        db.commit()
        db.refresh(new_board)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="A board with this name already exists.")
    return new_board

@router.get("/api/get_boards", response_model=List[schemas.BoardOut])
def get_boards(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Role check - only admin can view boards
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Only admin users can view boards")
    
    return db.query(models.Board).all()
