from db import get_connexion

try:
    conn = get_connexion()
    with conn.cursor() as cur:
        cur.execute("SELECT current_database(), current_user, version();")
        print(cur.fetchone())
    conn.close()
    print("Connexion OK")
except Exception as e:
    print("Erreur de connexion :", e)
