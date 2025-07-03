from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Ne pas supprimer, utilisé par FastAPI pour injecter les données du formulaire
from sqlalchemy.orm import Session

from app import schemas # Contient Token, User, UserCreate
from app.crud import user as crud_user_module # Accéder à l'instance 'user' via le module
from app.api import deps # Contient get_db, get_current_active_user
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User as UserModel # Pour le type hinting de current_user

router = APIRouter()

@router.post("/login/access-token", response_model=schemas.Token)
async def login_access_token( # Rendre async car les dépendances le sont
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends() # FastAPI gère ceci, form_data.username et form_data.password
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Prend 'username' et 'password' d'un formulaire x-www-form-urlencoded.
    'username' ici correspond à l'email de l'utilisateur.
    """
    user = crud_user_module.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, # Changé de 400 à 401 pour non autorisé
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not crud_user_module.user.is_active(user):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        user.email, expires_delta=access_token_expires # Utiliser l'email comme 'subject' du token
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.post("/login/test-token", response_model=schemas.User)
async def test_token(current_user: UserModel = Depends(deps.get_current_active_user)): # Rendre async
    """
    Test access token. Requiert un token valide.
    """
    return current_user

@router.post("/superuser-init", response_model=schemas.User, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(deps.get_db)]) # Assurer que la DB est prête
async def create_initial_superuser( # Rendre async
    db: Session = Depends(deps.get_db),
    # TODO: Idéalement, protéger cet endpoint ou le rendre disponible uniquement
    # sous certaines conditions (ex: aucune table User existante ou aucun superuser).
    # Pour l'instant, il est ouvert mais ne créera qu'une seule fois le superuser par défaut.
):
    """
    Create the first superuser if it doesn't exist.
    Utilise FIRST_SUPERUSER_EMAIL et FIRST_SUPERUSER_PASSWORD depuis la configuration.
    """
    existing_user = crud_user_module.user.get_by_email(db, email=settings.FIRST_SUPERUSER_EMAIL)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists. Superuser may have been initialized.",
        )

    user_in = schemas.UserCreate(
        email=settings.FIRST_SUPERUSER_EMAIL,
        password=settings.FIRST_SUPERUSER_PASSWORD,
        is_superuser=True,
        is_active=True, # Le premier superutilisateur doit être actif
        full_name="Initial Superuser"
    )
    try:
        superuser = crud_user_module.user.create(db, obj_in=user_in)
    except Exception as e: # Attraper les erreurs potentielles de la base de données
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create superuser: {e}",
        )
    return superuser

# On pourrait aussi ajouter un endpoint /users/me pour récupérer l'utilisateur courant
@router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: UserModel = Depends(deps.get_current_active_user)): # Rendre async
    """
    Get current logged in user.
    """
    return current_user
