import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_connexion():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode=os.getenv("DB_SSLMODE", "require"),
        options=f"-c search_path={os.getenv('DB_SCHEMA','public')}",
    )
