from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import bcrypt

from app.db import get_connexion

router = APIRouter(tags=["auth"])

class RegisterIn(BaseModel):
    entreprise_nom: str
    localisation: str | None = None
    login: str
    nom: str
    prenom: str
    tel: str | None = None
    email: str | None = None
    password: str

class LoginIn(BaseModel):
    login: str
    password: str

@router.post("/register")
def register(data: RegisterIn):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM istock.utilisateur WHERE login = %s", (data.login,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Login déjà utilisé.")

            cursor.execute("""
                INSERT INTO istock.entreprise (nom, localisation, proprietaire)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (data.entreprise_nom, data.localisation, data.login))
            entreprise_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO istock.employer (nom, prenom, num_tel, email, id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING ide
            """, (data.nom, data.prenom, data.tel, data.email, entreprise_id))
            employer_id = cursor.fetchone()[0]

            hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
            cursor.execute("""
                INSERT INTO istock.utilisateur (login, password_hash, role, entreprise_id, employer_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (data.login, hashed, "admin", entreprise_id, employer_id))

            conn.commit()
        return {"message": "Compte admin créé avec succès."}
    finally:
        conn.close()

@router.post("/login")
def login(data: LoginIn):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT password_hash, id, role, entreprise_id, employer_id
                FROM istock.utilisateur
                WHERE login = %s
            """, (data.login,))
            row = cursor.fetchone()

            if not row:
                raise HTTPException(status_code=404, detail="Utilisateur inconnu")

            password_hash, user_id, role, entreprise_id, employer_id = row
            if not bcrypt.checkpw(data.password.encode(), password_hash.encode()):
                raise HTTPException(status_code=401, detail="Mot de passe incorrect")

            prenom = None
            if employer_id is not None:
                cursor.execute("SELECT prenom FROM istock.employer WHERE ide = %s", (employer_id,))
                r = cursor.fetchone()
                if r:
                    prenom = r[0]

            return {
                "message": "Connexion réussie",
                "user_id": user_id,
                "role": role,
                "entreprise_id": entreprise_id,
                "employer_id": employer_id,
                "prenom": prenom
            }
    finally:
        conn.close()
