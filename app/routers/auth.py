from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas, utils, models, auth2
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy import select

router = APIRouter(
    tags=['Authentication']
)

@router.post('/api/login', response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Get user by email (username is used for email in this case)
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user or not utils.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid credentials"
        )

    # Generate JWT token
    access_token = auth2.create_access_token(data={"id": user.id})

    # Fetch user role
    user_role = db.query(models.UserRole.name).join(
        models.UserRoleRel, models.UserRole.id == models.UserRoleRel.role_id
    ).filter(models.UserRoleRel.user_id == user.id).first()
    message = "login successful"
    if user_role:
        role_name = user_role.name.lower()
        if role_name == "admin":
            message = "admin login successful"
        elif role_name == "teacher":
            message = "teacher login successful"
        elif role_name == "student":
            message = "student login successful"

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": message,
        "id": user.id
    }