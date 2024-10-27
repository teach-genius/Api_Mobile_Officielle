from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine


DATABASE_URL = "postgresql://postgres:SVDHfNkAPkqZOSJWUDSGmJFsXRCkyumL@autorack.proxy.rlwy.net:12391/railway"
# Configuration de l'URL de la base de données PostgreSQL
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
SECRET_KEY = "uF4Xf^WQm(YzmuF4Xf%5EWQ"
info_apk = {
    "main_window_title": "AryadMoney Software",
    "name_companie": "AryadMoney",
    "password_db": "SVDHfNkAPkqZOSJWUDSGmJFsXRCkyumL",
    "db_name": "railway",
    "user_name": "postgres",
    "host": "autorack.proxy.rlwy.net",
    "port": "12391",
}


"""
# Créer le moteur de base de données (assurez-vous de remplacer par votre URL de base de données)
engine = create_engine(DATABASE_URL)  # Remplacez par votre URL de base de données

# Supprimer les anciennes tables avec les dépendances
Base.metadata.drop_all(engine, checkfirst=True)
# Recréer les nouvelles tables
Base.metadata.create_all(engine)
"""
