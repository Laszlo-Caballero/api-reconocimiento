"""
Utilidades para inicializar la base de datos
"""
from database.db import PostgreDatabase
from modules.product.models.product import Product
from modules.product.models.image import ImageData
from modules.product.models.image_product import ImageProduct


def init_db():
    """Crear todas las tablas en la base de datos"""
    db = PostgreDatabase()
    
    # Importar Base desde los modelos
    from database.base import Base
    
    print("Creando tablas...")
    Base.metadata.create_all(bind=db.engine)
    print("Tablas creadas exitosamente.")


def drop_db():
    """Eliminar todas las tablas de la base de datos (usar con cuidado)"""
    db = PostgreDatabase()
    
    from database.base import Base
    
    print("Eliminando tablas...")
    Base.metadata.drop_all(bind=db.engine)
    print("Tablas eliminadas exitosamente.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        drop_db()
    else:
        init_db()
