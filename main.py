from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from routes import user_routes, question_routes, forum_routes, resource_routes
from jwt_utils import JWTMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(JWTMiddleware)
app.include_router(user_routes.router, prefix="/api")
app.include_router(question_routes.router, prefix="/api")
app.include_router(forum_routes.router, prefix="/api")
app.include_router(resource_routes.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de la plataforma de aprendizaje"}
