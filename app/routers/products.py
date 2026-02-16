from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.db import get_connexion

router = APIRouter(tags=["products"])

class ProductIn(BaseModel):
    nom: str
    description: str | None = None
    prix: float
    qte: int
    entreprise_id: int
    employer_id: int

class UpdateQuantityIn(BaseModel):
    idp: int
    nouvelle_qte: int
    employer_id: int

@router.post("/add-product")
def add_product(data: ProductIn):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO istock.produit (nom, description, prix, qte, id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING idp
            """, (data.nom, data.description, data.prix, data.qte, data.entreprise_id))
            idp = cursor.fetchone()[0]

            cursor.execute("INSERT INTO istock.ajouter (idp, ide) VALUES (%s, %s)", (idp, data.employer_id))
            conn.commit()

        return {"message": "Produit ajouté avec succès.", "idp": idp}
    finally:
        conn.close()

@router.get("/articles")
def get_articles(entreprise_id: int = Query(...)):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT idp, nom, description, prix, qte
                FROM istock.produit
                WHERE id = %s
            """, (entreprise_id,))
            rows = cursor.fetchall()

        return [
            {"idp": r[0], "nom": r[1], "description": r[2], "prix": float(r[3]), "qte": r[4]}
            for r in rows
        ]
    finally:
        conn.close()

@router.post("/update-quantity")
def update_quantity(data: UpdateQuantityIn):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT qte FROM istock.produit WHERE idp = %s", (data.idp,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Produit introuvable")
            ancienne_qte = row[0]

            cursor.execute("UPDATE istock.produit SET qte = %s WHERE idp = %s", (data.nouvelle_qte, data.idp))

            cursor.execute("""
                INSERT INTO istock.historique_mouvement (idp, ide, ancienne_qte, nouvelle_qte)
                VALUES (%s, %s, %s, %s)
            """, (data.idp, data.employer_id, ancienne_qte, data.nouvelle_qte))

            conn.commit()

        return {"message": "Quantité mise à jour avec succès."}
    finally:
        conn.close()
