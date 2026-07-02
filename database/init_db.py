"""
Utilidades para inicializar la base de datos
"""
from database.db import PostgreDatabase
from modules.product.models.product import Product
from modules.product.models.image import ImageData
from modules.product.models.tienda import Tienda
from modules.promotion.models.promotion_model import Promotion, SurprisePromotion


def init_db():
    """Crear todas las tablas en la base de datos"""
    db = PostgreDatabase()
    
    # Importar Base desde los modelos
    from database.base import Base
    
    print("Creando tablas...")
    Base.metadata.create_all(bind=db.engine)
    print("Tablas creadas exitosamente.")

    # Seeding surprise promotions
    session = db.get_session()
    try:
        count = session.query(SurprisePromotion).count()
        if count == 0:
            print("Sembrando promociones sorpresa...")
            surprises = [
                SurprisePromotion(
                    title="Bono Misterioso 🎁",
                    description="¡Felicidades! Has desbloqueado un cupón misterioso del 15% de descuento en toda la tienda.",
                    qr_code_url="/images/promotions/mystery_gift.png"
                ),
                SurprisePromotion(
                    title="Super Bono de Caja Chica ⚡",
                    description="¡Escaneo de la suerte! Recibe S/ 20 de descuento directo en tu siguiente ticket mayor a S/ 100.",
                    qr_code_url="/images/promotions/lucky_strike.png"
                ),
                SurprisePromotion(
                    title="Recompensa Eco-Amigable 🌱",
                    description="¡Gracias por preferirnos! Llévate una bolsa reutilizable gratis en tu compra superior a S/ 50.",
                    qr_code_url="/images/promotions/eco_bonus.png"
                )
            ]
            session.add_all(surprises)
            session.commit()
            print("Promociones sorpresa sembradas exitosamente.")
    except Exception as e:
        session.rollback()
        print(f"Error al sembrar promociones sorpresa: {e}")
    finally:
        session.close()


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
