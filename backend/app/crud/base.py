from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

from app.db.base import Base # Votre classe de base SQLAlchemy

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = "desc" # "asc" ou "desc"
    ) -> List[ModelType]:
        query = db.query(self.model)

        if sort_by and hasattr(self.model, sort_by):
            try: # Essayer d'accéder à l'attribut pour s'assurer qu'il est chargeable/valide pour le tri
                column_to_sort = getattr(self.model, sort_by)
                if sort_order.lower() == "asc":
                    query = query.order_by(asc(column_to_sort))
                else:
                    query = query.order_by(desc(column_to_sort))
            except Exception: # Si l'attribut n'est pas valide pour le tri (ex: relation non chargée)
                # Option: logguer une erreur ou trier par défaut
                query = query.order_by(desc(self.model.id)) # Tri par défaut par ID si sort_by échoue
        else:
            # Tri par défaut si sort_by n'est pas fourni ou n'est pas un attribut valide
            if hasattr(self.model, 'created_at'):
                query = query.order_by(desc(self.model.created_at))
            else:
                query = query.order_by(desc(self.model.id))


        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        # Pydantic V2: obj_in_data = obj_in.model_dump()
        # Pydantic V1: obj_in_data = obj_in.dict()
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        # Convertit l'objet SQLAlchemy en dict pour une itération facile des champs
        # jsonable_encoder est utile car il gère les types complexes comme datetime
        obj_data = jsonable_encoder(db_obj)

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Pydantic V2: update_data = obj_in.model_dump(exclude_unset=True) # N'inclut que les champs explicitement définis
            # Pydantic V1: update_data = obj_in.dict(exclude_unset=True)
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data: # Itère sur les champs du modèle existant
            if field in update_data and update_data[field] is not None: # Si le champ est dans les données de mise à jour et non None
                setattr(db_obj, field, update_data[field])

        db.add(db_obj) # Ajoute l'objet à la session (nécessaire si l'objet était détaché ou pour marquer comme dirty)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        obj = db.query(self.model).get(id) # .get() est un raccourci pour .filter(self.model.id == id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj # Retourne l'objet supprimé (ou None s'il n'a pas été trouvé)
