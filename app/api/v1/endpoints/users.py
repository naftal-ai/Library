from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_active_superuser, get_current_active_user
from app.core.exceptions import BadRequestError, NotFoundError
from app.crud.user import user
from app.db.session import get_db
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter()


@router.get("/", response_model=List[User])
def read_users(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    users = user.get_multi(db, skip=skip, limit=limit)
    return users


@router.post("/", response_model=User)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user_exists = user.get_by_email(db, email=user_in.email)
    if user_exists:
        raise BadRequestError(
            detail="The user with this email already exists in the system"
        )
    
    username_exists = user.get_by_username(db, username=user_in.username)
    if username_exists:
        raise BadRequestError(
            detail="The user with this username already exists in the system"
        )
    
    user_obj = user.create(db, obj_in=user_in)
    return user_obj


@router.get("/me", response_model=User)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=User)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user.
    """
    # Check if email already exists
    if user_in.email and user_in.email != current_user.email:
        user_exists = user.get_by_email(db, email=user_in.email)
        if user_exists:
            raise BadRequestError(
                detail="The user with this email already exists in the system"
            )
    
    # Check if username already exists
    if user_in.username and user_in.username != current_user.username:
        username_exists = user.get_by_username(db, username=user_in.username)
        if username_exists:
            raise BadRequestError(
                detail="The user with this username already exists in the system"
            )
    
    user_obj = user.update(db, db_obj=current_user, obj_in=user_in)
    return user_obj


@router.get("/{user_id}", response_model=User)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    """
    user_obj = user.get(db, id=user_id)
    if not user_obj:
        raise NotFoundError(detail="User not found")
    
    if user_obj.id != current_user.id and not user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return user_obj


@router.put("/{user_id}", response_model=User)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user_obj = user.get(db, id=user_id)
    if not user_obj:
        raise NotFoundError(detail="User not found")
    
    # Check if email already exists
    if user_in.email and user_in.email != user_obj.email:
        user_exists = user.get_by_email(db, email=user_in.email)
        if user_exists:
            raise BadRequestError(
                detail="The user with this email already exists in the system"
            )
    
    # Check if username already exists
    if user_in.username and user_in.username != user_obj.username:
        username_exists = user.get_by_username(db, username=user_in.username)
        if username_exists:
            raise BadRequestError(
                detail="The user with this username already exists in the system"
            )
    
    user_obj = user.update(db, db_obj=user_obj, obj_in=user_in)
    return user_obj


@router.delete("/{user_id}", response_model=User)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Delete a user.
    """
    user_obj = user.get(db, id=user_id)
    if not user_obj:
        raise NotFoundError(detail="User not found")
    
    user_obj = user.remove(db, id=user_id)
    return user_obj
