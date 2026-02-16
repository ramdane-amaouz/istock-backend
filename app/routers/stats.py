from fastapi import APIRouter, Query
from app.db import get_connexion

router = APIRouter(tags=["stats"])

@router.get("/stats")
def get_stats(entreprise_id: int = Query(...)):
    conn = get_connexion()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM istock.produit WHERE id = %s", (entreprise_id,))
            nb_produits = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM istock.employer WHERE id = %s", (entreprise_id,))
            nb_employes = cursor.fetchone()[0]

        return {"nb_produits": nb_produits, "nb_employes": nb_employes}
    finally:
        conn.close()
