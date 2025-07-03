from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import ValidationError # Gardez cette importation si TokenData peut lever ValidationError

from app.core.config import settings
from app.schemas.token import TokenData # Assurez-vous que ce schéma est défini

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM # Défini dans config.py
SECRET_KEY = settings.SECRET_KEY # Défini dans config.py

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception: # passlib peut lever différentes erreurs pour des hash invalides
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Optionnel: Fonction pour décoder le token et valider (utilisé dans deps.py)
# Retourne l'email (ou l'identifiant stocké dans 'sub') ou lève une exception
def get_subject_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            raise JWTError("User identifier (sub) not in token payload")
        # Vous pourriez vouloir valider le format de 'subject' ici si c'est un email, etc.
        # Pour l'instant, on retourne juste la chaîne.
        return str(subject)
    except JWTError as e: # Attrape les erreurs spécifiques à JWT (format, signature, expiration)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Could not validate credentials: {str(e)}",
        )
    except Exception: # Attrape d'autres erreurs potentielles
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials, unexpected error",
        )

# Note: J'ai importé HTTPException et status ici car get_subject_from_token les utilise.
# Il serait peut-être plus propre de laisser cette fonction retourner None ou lever une exception personnalisée
# et de gérer la HTTPException dans la dépendance FastAPI elle-même.
# Pour l'instant, je vais le laisser comme ça, mais c'est un point à considérer pour le refactoring.
# Pour éviter la dépendance circulaire (deps -> security -> deps), je vais retirer HTTPException d'ici.
# La fonction lèvera JWTError ou une autre exception, et deps.py la gérera.

# Version modifiée de get_subject_from_token sans HTTPException:
def get_subject_from_token_v2(token: str) -> Optional[str]: # Renommé pour éviter conflit si l'ancienne est en cache
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        subject = payload.get("sub")
        if subject is None:
            # Lever une exception spécifique ou retourner None
            # Pour la cohérence avec le code dans deps.py, JWTError est approprié
            raise JWTError("User identifier (sub) not in token payload")
        return str(subject)
    except JWTError:
        # Laisser l'appelant (deps.py) gérer la transformation en HTTPException
        raise # Relance l'exception JWTError
    # Pas besoin de ValidationError ici si TokenData n'est pas construit.
    # Pas besoin d'AttributeError ici.
```

Je vais utiliser `get_subject_from_token_v2` dans `deps.py`. Je dois aussi importer `HTTPException` et `status` dans `security.py` si je garde la première version de `get_subject_from_token`. Pour éviter les dépendances circulaires et garder la logique HTTP dans les couches API/dépendances, je vais opter pour `get_subject_from_token_v2` et gérer les `HTTPException` dans `deps.py`.
