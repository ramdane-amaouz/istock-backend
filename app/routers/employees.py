from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import bcrypt

from app.db import get_connexion

router = APIRouter(tags=["employees"])

class EmployeeCreateIn(BaseModel):
    nom: str
    prenom: str
    tel: str | None = None
    email: str | None = None
    login: str
    password: str
    entreprise_id: int
    role: str = "employe"

class EmployeeUpdateIn(BaseModel):
    ide: int
    nom: str
    prenom: str
    tel: str | None = None
    email: str | None = None
    role: str
    utilisateur_id: int

@router.post("/add-employee")
def add_employee(data: EmployeeCreateIn):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM istock.utilisateur WHERE login = %s", (data.login,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Login déjà utilisé.")

            cursor.execute("""
                INSERT INTO istock.employer (nom, prenom, num_tel, email, id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING ide
            """, (data.nom, data.prenom, data.tel, data.email, data.entreprise_id))
            employer_id = cursor.fetchone()[0]

            hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
            cursor.execute("""
                INSERT INTO istock.utilisateur (login, password_hash, role, entreprise_id, employer_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (data.login, hashed, data.role, data.entreprise_id, employer_id))

            conn.commit()
        return {"message": "Employé créé avec succès."}
    finally:
        conn.close()

@router.get("/employes")
def get_employes(entreprise_id: int = Query(...)):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT e.ide, e.nom, e.prenom, e.num_tel, e.email, u.role, u.id as utilisateur_id
                FROM istock.employer e
                JOIN istock.utilisateur u ON u.employer_id = e.ide
                WHERE e.id = %s
            """, (entreprise_id,))
            rows = cursor.fetchall()

        return [
            {
                "ide": r[0],
                "nom": r[1],
                "prenom": r[2],
                "tel": r[3],
                "email": r[4],
                "role": r[5],
                "utilisateur_id": r[6],
            }
            for r in rows
        ]
    finally:
        conn.close()

@router.post("/update-employe")
def update_employe(data: EmployeeUpdateIn):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE istock.employer
                SET nom = %s, prenom = %s, num_tel = %s, email = %s
                WHERE ide = %s
            """, (data.nom, data.prenom, data.tel, data.email, data.ide))

            cursor.execute("""
                UPDATE istock.utilisateur
                SET role = %s
                WHERE id = %s
            """, (data.role, data.utilisateur_id))

            conn.commit()

        return {"message": "Employé mis à jour avec succès."}
    finally:
        conn.close()

@router.delete("/delete-employe/{ide}")
def delete_employe(ide: int):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM istock.utilisateur WHERE employer_id = %s", (ide,))
            cursor.execute("DELETE FROM istock.employer WHERE ide = %s", (ide,))
            conn.commit()
        return {"message": "Employé supprimé avec succès."}
    finally:
        conn.close()
