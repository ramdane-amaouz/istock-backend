from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg
import bcrypt

app = Flask(__name__)
#CORS(app, origins=["https://istock-front.netlify.app"])
# Remplace ta ligne actuelle par celle-ci pour autoriser ton frontend local :
CORS(app, origins=["https://istock-front.netlify.app", "http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:8000/"])

def get_connexion():
    return psycopg.connect(
        host="bd-pedago.univ-lyon1.fr",
        user="p2002623",
        password="Reuse46Simile",
        dbname="p2002623",
        options="-c search_path=istock"
    )

@app.route("/", methods=["GET"])
def home():
    return "API iStock opérationnelle 🚀"

@app.route("/register", methods=["POST"])
def register():
    data = request.json

    entreprise_nom = data["entreprise_nom"]
    localisation = data["localisation"]
    proprietaire = data["login"]

    nom = data["nom"]
    prenom = data["prenom"]
    tel = data["tel"]
    email = data["email"]

    login_user = data["login"]
    password_input = data["password"]

    conn = get_connexion()
    with conn.cursor() as cursor:
        # Vérifier si le login existe déjà
        cursor.execute("""
            SELECT id FROM istock.utilisateur
            WHERE login = %s
        """, (login_user,))
        if cursor.fetchone():
            return jsonify({"message": "Login déjà utilisé."}), 409

        # Créer entreprise → récupérer id SERIAL
        cursor.execute("""
            INSERT INTO istock.entreprise (nom, localisation, proprietaire)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (entreprise_nom, localisation, proprietaire))
        entreprise_id = cursor.fetchone()[0]

        # Créer l'employé admin → récupérer ide
        cursor.execute("""
            INSERT INTO istock.employer (nom, prenom, num_tel, email, id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING ide
        """, (nom, prenom, tel, email, entreprise_id))
        employer_id = cursor.fetchone()[0]

        # Créer l'utilisateur admin
        hashed = bcrypt.hashpw(password_input.encode(), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO istock.utilisateur (login, password_hash, role, entreprise_id, employer_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (login_user, hashed.decode(), 'admin', entreprise_id, employer_id))

        conn.commit()

    return jsonify({"message": "Compte admin créé avec succès."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    login_user = data["login"]
    password_input = data["password"]

    conn = get_connexion()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT password_hash, id, role, entreprise_id, employer_id
            FROM istock.utilisateur
            WHERE login = %s
        """, (login_user,))
        row = cursor.fetchone()

        if row:
            password_hash, user_id, role, entreprise_id, employer_id = row

            if bcrypt.checkpw(password_input.encode(), password_hash.encode()):
                # Chercher le prénom si employer_id existe
                prenom = None
                if employer_id is not None:
                    cursor.execute("""
                        SELECT prenom
                        FROM istock.employer
                        WHERE ide = %s
                    """, (employer_id,))
                    prenom_row = cursor.fetchone()
                    if prenom_row:
                        prenom = prenom_row[0]

                return jsonify({
                    "message": "Connexion réussie",
                    "user_id": user_id,
                    "role": role,
                    "entreprise_id": entreprise_id,
                    "employer_id": employer_id,
                    "prenom": prenom
                })
            else:
                return jsonify({"message": "Mot de passe incorrect"}), 401
        else:
            return jsonify({"message": "Utilisateur inconnu"}), 404

@app.route("/add-product", methods=["POST"])
def add_product():
    data = request.json

    nom = data["nom"]
    description = data["description"]
    prix = data["prix"]
    qte = data["qte"]
    entreprise_id = data["entreprise_id"]
    employer_id = data["employer_id"]

    conn = get_connexion()
    with conn.cursor() as cursor:
        # Insérer produit
        cursor.execute("""
            INSERT INTO istock.produit (nom, description, prix, qte, id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING idp
        """, (nom, description, prix, qte, entreprise_id))

        idp = cursor.fetchone()[0]

        # Insérer dans ajouter
        cursor.execute("""
            INSERT INTO istock.ajouter (idp, ide)
            VALUES (%s, %s)
        """, (idp, employer_id))

        conn.commit()

    return jsonify({"message": "Produit ajouté avec succès.", "idp": idp})

@app.route("/add-employee", methods=["POST"])
def add_employee():
    data = request.json

    nom = data["nom"]
    prenom = data["prenom"]
    tel = data["tel"]
    email = data["email"]
    login_user = data["login"]
    password_input = data["password"]
    entreprise_id = data["entreprise_id"]
    role = data.get("role", "employe")

    conn = get_connexion()
    with conn.cursor() as cursor:
        # Vérifier si login déjà pris
        cursor.execute("""
            SELECT id FROM istock.utilisateur WHERE login = %s
        """, (login_user,))
        if cursor.fetchone():
            return jsonify({"message": "Login déjà utilisé."}), 409

        # Créer l'employé
        cursor.execute("""
            INSERT INTO istock.employer (nom, prenom, num_tel, email, id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING ide
        """, (nom, prenom, tel, email, entreprise_id))
        employer_id = cursor.fetchone()[0]

        # Créer l'utilisateur lié à cet employé
        hashed = bcrypt.hashpw(password_input.encode(), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO istock.utilisateur (login, password_hash, role, entreprise_id, employer_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (login_user, hashed.decode(), role, entreprise_id, employer_id))

        conn.commit()

    return jsonify({"message": "Employé créé avec succès."})

@app.route("/articles", methods=["GET"])
def get_articles():
    entreprise_id = request.args.get("entreprise_id")

    conn = get_connexion()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT idp, nom, description, prix, qte
            FROM istock.produit
            WHERE id = %s
        """, (entreprise_id,))
        rows = cursor.fetchall()

    articles = []
    for row in rows:
        articles.append({
            "idp": row[0],
            "nom": row[1],
            "description": row[2],
            "prix": float(row[3]),
            "qte": row[4]
        })

    return jsonify(articles)

@app.route("/update-quantity", methods=["POST"])
def update_quantity():
    data = request.json

    idp = data["idp"]
    nouvelle_qte = data["nouvelle_qte"]
    employer_id = data["employer_id"]

    conn = get_connexion()
    with conn.cursor() as cursor:
        # récupérer l'ancienne quantité
        cursor.execute("""
            SELECT qte FROM istock.produit WHERE idp = %s
        """, (idp,))
        row = cursor.fetchone()
        ancienne_qte = row[0] if row else None

        # mettre à jour la table produit
        cursor.execute("""
            UPDATE istock.produit
            SET qte = %s
            WHERE idp = %s
        """, (nouvelle_qte, idp))

        # insérer dans historique
        cursor.execute("""
            INSERT INTO istock.historique_mouvement
            (idp, ide, ancienne_qte, nouvelle_qte)
            VALUES (%s, %s, %s, %s)
        """, (idp, employer_id, ancienne_qte, nouvelle_qte))

        conn.commit()

    return jsonify({"message": "Quantité mise à jour avec succès."})

@app.route("/employes", methods=["GET"])
def get_employes():
    entreprise_id = request.args.get("entreprise_id")

    conn = get_connexion()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT e.ide, e.nom, e.prenom, e.num_tel, e.email, u.role, u.id as utilisateur_id
            FROM istock.employer e
            JOIN istock.utilisateur u ON u.employer_id = e.ide
            WHERE e.id = %s
        """, (entreprise_id,))
        rows = cursor.fetchall()

    employes = []
    for row in rows:
        employes.append({
            "ide": row[0],
            "nom": row[1],
            "prenom": row[2],
            "tel": row[3],
            "email": row[4],
            "role": row[5],
            "utilisateur_id": row[6]
        })

    return jsonify(employes)

@app.route("/update-employe", methods=["POST"])
def update_employe():
    data = request.json

    ide = data["ide"]
    nom = data["nom"]
    prenom = data["prenom"]
    tel = data["tel"]
    email = data["email"]
    role = data["role"]
    utilisateur_id = data["utilisateur_id"]

    conn = get_connexion()
    with conn.cursor() as cursor:
        # mettre à jour employer
        cursor.execute("""
            UPDATE istock.employer
            SET nom = %s, prenom = %s, num_tel = %s, email = %s
            WHERE ide = %s
        """, (nom, prenom, tel, email, ide))

        # mettre à jour utilisateur (rôle)
        cursor.execute("""
            UPDATE istock.utilisateur
            SET role = %s
            WHERE id = %s
        """, (role, utilisateur_id))

        conn.commit()

    return jsonify({"message": "Employé mis à jour avec succès."})

@app.route("/delete-employe/<int:ide>", methods=["DELETE"])
def delete_employe(ide):
    conn = get_connexion()
    with conn.cursor() as cursor:
        # supprimer d'abord dans utilisateur
        cursor.execute("""
            DELETE FROM istock.utilisateur
            WHERE employer_id = %s
        """, (ide,))

        # puis dans employer
        cursor.execute("""
            DELETE FROM istock.employer
            WHERE ide = %s
        """, (ide,))

        conn.commit()

    return jsonify({"message": "Employé supprimé avec succès."})

@app.route("/stats", methods=["GET"])
def get_stats():
    entreprise_id = request.args.get("entreprise_id")

    conn = get_connexion()
    with conn.cursor() as cursor:
        # Nombre de produits
        cursor.execute("""
            SELECT COUNT(*) FROM istock.produit
            WHERE id = %s
        """, (entreprise_id,))
        nb_produits = cursor.fetchone()[0]

        # Nombre d'employés
        cursor.execute("""
            SELECT COUNT(*) FROM istock.employer
            WHERE id = %s
        """, (entreprise_id,))
        nb_employes = cursor.fetchone()[0]

    return jsonify({
        "nb_produits": nb_produits,
        "nb_employes": nb_employes
    })


# ✅ ✅ CORRECTION POUR RENDER
import os

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
