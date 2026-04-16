from fastapi import Header, HTTPException
import jwt # pyjwt

SECRET = SUPABASE_JWT_SECRET

async def get_current_user(authorization: str = Header(...)):
    token = authorization.split(" ")[1]
    try:
        # Vérification du token Supabase
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Token invalide")