from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse

SECRET_KEY = "clave_secreta_super_segura"
ALGORITHM = "HS256"
EXPIRATION_MINUTES = 60 * 24
EXCLUDED_PATHS = [
    "/api/login",
    "/api/register_user",
    "/api/verify_user",
]

def crear_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


class JWTMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            if request.method == "OPTIONS":
                return await call_next(request)
        
            if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
                return await call_next(request)

            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Token faltante o inválido")

            token = auth_header.split(" ")[1]
            payload = verificar_token(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Token inválido o expirado")

            request.state.user = payload
            response = await call_next(request)
            return response
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        except Exception as e:
            return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})
