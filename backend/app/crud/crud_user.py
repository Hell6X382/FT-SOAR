from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session
from pydantic import EmailStr

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate # Pydantic schemas

class CRUDUser:
    def get(self, db: Session, id: Any) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()

    def get_by_email(self, db: Session, *, email: EmailStr) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser if obj_in.is_superuser is not None else False,
            is_active=obj_in.is_active if obj_in.is_active is not None else True,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) # Pydantic V2 (V1: .dict())

        if "password" in update_data and update_data["password"]:
            # Si un nouveau mot de passe est fourni et n'est pas None/vide
            hashed_password = get_password_hash(update_data["password"])
            db_obj.hashed_password = hashed_password
            del update_data["password"] # Retirer pour ne pas l'assigner directement ci-dessous

        # Mettre à jour les autres champs
        for field, value in update_data.items():
            if hasattr(db_obj, field): # Vérifier si l'attribut existe sur le modèle
                setattr(db_obj, field, value)

        db.add(db_obj) # ou db.merge(db_obj) si db_obj n'est pas déjà dans la session
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[User]:
        obj = db.query(User).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj # Retourne l'objet supprimé ou None

    def authenticate(
        self, db: Session, *, email: EmailStr, password: str
    ) -> Optional[User]:
        user_obj = self.get_by_email(db, email=email)
        if not user_obj:
            return None
        if not verify_password(password, user_obj.hashed_password):
            return None
        return user_obj

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

user = CRUDUser() # Singleton instance pour un accès facile (ex: crud.user.get(...))
