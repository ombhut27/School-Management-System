from fastapi import FastAPI, Depends, HTTPException, status,APIRouter
from sqlalchemy.orm import Session
from app import models, schemas, utils
from app.utils import hash
from app.database import get_db
from app.auth2 import get_current_user
from sqlalchemy import select

router = APIRouter()


@router.get("/api/get_users", response_model=list[schemas.UserOut])
def get_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Allow only admin
    user_role_rel = db.query(models.UserRoleRel).filter(models.UserRoleRel.user_id == current_user.id).first()
    if not user_role_rel:
        raise HTTPException(status_code=403, detail="User does not have a role assigned")
    role = db.query(models.UserRole).filter(models.UserRole.id == user_role_rel.role_id).first()
    if not role or role.name.lower() != "admin":
        raise HTTPException(status_code=403, detail="Only admin users can view users")

    users = db.query(models.User).all()
    return users

@router.post("/api/create_teacher", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
async def create_teacher(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        current_user = db.query(models.User).filter(models.User.email == user.email).first()
        if current_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
        
        # Hash the password
        hashed_password = hash(user.password)
        user.password = hashed_password

        # Create the user
        new_user = models.User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Assign the "Teacher" role
        teacher_role = db.query(models.UserRole).filter(models.UserRole.name == "teacher").first()
        if not teacher_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher role does not exist")

        user_role_rel = models.UserRoleRel(user_id=new_user.id, role_id=teacher_role.id)
        db.add(user_role_rel)
        db.commit()

        return new_user
    except HTTPException:
        # Re-raise HTTPExceptions so FastAPI handles them as intended
        raise
    except Exception as e:
        # Catch all other exceptions and return a 500 error
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/api/create_student", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
async def create_student(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        current_user = db.query(models.User).filter(models.User.email == user.email).first()
        if current_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
        
        # Hash the password
        hashed_password = hash(user.password)
        user.password = hashed_password

        # Create the user
        new_user = models.User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Assign the "student" role
        student_role = db.query(models.UserRole).filter(models.UserRole.name == "student").first()
        if not student_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student role does not exist")

        user_role_rel = models.UserRoleRel(user_id=new_user.id, role_id=student_role.id)
        db.add(user_role_rel)
        db.commit()

        return new_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/api/create_admin", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
async def create_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email already exists
        current_user = db.query(models.User).filter(models.User.email == user.email).first()
        if current_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="email already exists")
        
        # Hash the password
        hashed_password = hash(user.password)
        user.password = hashed_password

        # Create the user
        new_user = models.User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Assign the "admin" role
        admin_role = db.query(models.UserRole).filter(models.UserRole.name == "admin").first()
        if not admin_role:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin role does not exist")

        user_role_rel = models.UserRoleRel(user_id=new_user.id, role_id=admin_role.id)
        db.add(user_role_rel)
        db.commit()

        return new_user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


