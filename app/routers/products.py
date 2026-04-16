from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from app.db import get_connexion

router = APIRouter(tags=["products"])


# -------------------------
# Pydantic models
# -------------------------
class ProductIn(BaseModel):
    nom: str = Field(..., min_length=1)
    description: str | None = None
    prix: float = Field(..., ge=0)
    qte: int = Field(..., ge=0)
    entreprise_id: int
    employer_id: int
    categorie: str = Field(..., min_length=1)


class UpdateQuantityIn(BaseModel):
    idp: int
    nouvelle_qte: int = Field(..., ge=0)
    employer_id: int


# -------------------------
# Routes
# -------------------------
@router.post("/add-product")
def add_product(data: ProductIn):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            # Normalisation simple (optionnel mais pratique)
            categorie = data.categorie.strip()

            cursor.execute(
                """
                INSERT INTO istock.produit (nom, description, prix, qte, id, categorie)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING idp
                """,
                (data.nom, data.description, data.prix, data.qte, data.entreprise_id, categorie),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Insertion échouée (idp non retourné).")
            idp = row[0]

            cursor.execute(
                "INSERT INTO istock.ajouter (idp, ide) VALUES (%s, %s)",
                (idp, data.employer_id),
            )

            conn.commit()

        return {"message": "Produit ajouté avec succès.", "idp": idp}
    finally:
        conn.close()


@router.get("/articles")
def get_articles(
    entreprise_id: int = Query(...),
    categorie: Optional[str] = Query(None),
):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            if categorie and categorie.strip():
                cursor.execute(
                    """
                    SELECT idp, nom, categorie, prix, qte
                    FROM istock.produit
                    WHERE id = %s AND categorie = %s
                    ORDER BY nom
                    """,
                    (entreprise_id, categorie.strip()),
                )
            else:
                cursor.execute(
                    """
                    SELECT idp, nom, categorie, prix, qte
                    FROM istock.produit
                    WHERE id = %s
                    ORDER BY nom
                    """,
                    (entreprise_id,),
                )

            rows = cursor.fetchall()

        return [
            {
                "idp": r[0],
                "nom": r[1],
                "categorie": r[2],
                "prix": float(r[3]),
                "qte": r[4],
            }
            for r in rows
        ]
    finally:
        conn.close()


@router.get("/categories")
def get_categories(entreprise_id: int = Query(...)):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT categorie
                FROM istock.produit
                WHERE id = %s
                  AND categorie IS NOT NULL
                  AND btrim(categorie) <> ''
                ORDER BY categorie
                """,
                (entreprise_id,),
            )
            rows = cursor.fetchall()

        # Renvoie une liste de strings: ["Boissons", "Snacks", ...]
        return [r[0] for r in rows]
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

            cursor.execute(
                "UPDATE istock.produit SET qte = %s WHERE idp = %s",
                (data.nouvelle_qte, data.idp),
            )

            cursor.execute(
                """
                INSERT INTO istock.historique_mouvement (idp, ide, ancienne_qte, nouvelle_qte)
                VALUES (%s, %s, %s, %s)
                """,
                (data.idp, data.employer_id, ancienne_qte, data.nouvelle_qte),
            )

            conn.commit()

        return {"message": "Quantité mise à jour avec succès."}
    finally:
        conn.close()
