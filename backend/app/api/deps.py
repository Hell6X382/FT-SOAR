from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from pydantic import EmailStr, ValidationError # Pour valider l'email si besoin

from app.core.config import settings
from app.core.security import get_subject_from_token # Utilise la version qui lève JWTError
from app.db.session import SessionLocal
from app.models.user import User
from app.crud import user as crud_user_module # Importer le module crud.user
# from app.schemas.token import TokenData # Plus nécessaire ici si on utilise get_subject_from_token

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token",
    auto_error=False # Important: Mettre à False pour gérer l'erreur manuellement et retourner une réponse JSON
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user( # Rendre la fonction async si reusable_oauth2 est appelé avec await
    db: Session = Depends(get_db), token: Optional[str] = Depends(reusable_oauth2)
) -> Optional[User]:
    if not token:
        # Si auto_error=True, FastAPI lèverait une erreur 401 ici.
        # Avec auto_error=False, token peut être None si l'en-tête Authorization est manquant.
        # On peut choisir de lever une erreur ici ou de laisser certaines routes être optionnellement authentifiées.
        # Pour les routes protégées, on lèvera une erreur si pas de token.
        # Cette fonction peut retourner None, et les endpoints vérifieront.
        # Ou on peut lever l'exception ici directement:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        # return None # Alternative si on veut gérer l'absence de token plus tard

    try:
        user_email_str = get_subject_from_token(token)
        # Optionnel: valider que c'est bien un email
        try:
            user_email = EmailStr.validate(user_email_str)
        except ValidationError: # Pydantic ValidationError
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user identifier in token (not an email)",
            )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, # 403 car un token a été fourni mais il est invalide/expiré
            detail=f"Could not validate credentials: {e}", # Inclure le message de JWTError peut être utile pour le débogage
            headers={"WWW-Authenticate": "Bearer"}, # Indique que l'authentification Bearer est attendue
        )

    user = crud_user_module.user.get_by_email(db, email=user_email) # Utilise l'instance 'user' du module crud_user
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

async def get_current_active_user( # Rendre async
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user: # current_user peut être None si get_current_user est modifié pour retourner None
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if not crud_user_module.user.is_active(current_user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

async def get_current_active_superuser( # Rendre async
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not crud_user_module.user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="The user doesn't have enough privileges"
        )
    return current_user
