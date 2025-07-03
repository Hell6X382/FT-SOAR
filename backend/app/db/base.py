from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime, timezone
import re

@as_declarative()
class Base:
    """
    Base class which provides automated table name
    and surrogate primary key column.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        # Convertit CamelCase en snake_case et ajoute un 's' pour le pluriel
        # Exemple: IncidentNote -> incident_notes, User -> users
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        if not name.endswith('s'):
            # Cas simples comme 'user' -> 'users', 'status' -> 'statuses'
            if name.endswith('y') and not name.endswith('ey'): # Ex: 'category' -> 'categories'
                name = name[:-1] + 'ies'
            elif name.endswith('s') or name.endswith('sh') or name.endswith('ch') or name.endswith('x') or name.endswith('z'):
                name = name + 'es' # Ex: 'status' -> 'statuses'
            else:
                name = name + 's'
        return name

    id = Column(Integer, primary_key=True, index=True)
    # Utiliser timezone.utc pour s'assurer que les datetimes sont timezone-aware (UTC)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

# Importez tous les modèles ici pour que Base les connaisse avant d'appeler create_all
# Ceci est crucial pour que `Base.metadata.create_all(engine)` fonctionne correctement.
# Par exemple:
# from app.models.user import User
# from app.models.incident import Incident, IncidentNote
# etc.

# Vous pouvez également créer une fonction `init_models()` qui importe tous les modèles
# et l'appeler avant `create_all`.

# Ou, plus simplement, assurez-vous que les modules contenant vos modèles sont importés
# quelque part dans votre application avant que `create_db_and_tables` soit appelé.
# Par exemple, dans `main.py` ou dans `db.base_class` (ce fichier) si vous importez
# les modèles ici.

# Pour la simplicité de l'exemple initial, nous allons les importer dans main.py avant create_all.
