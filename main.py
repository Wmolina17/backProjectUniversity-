from fastapi import FastAPI
from routes import user_routes, question_routes, forum_routes, resource_routes, project_routes
from fastapi.middleware.cors import CORSMiddleware
from database import db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_routes.router, prefix="/api")
app.include_router(question_routes.router, prefix="/api")
# app.include_router(forum_routes.router, prefix="/api")
# app.include_router(resource_routes.router, prefix="/api")
# app.include_router(project_routes.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de la plataforma de aprendizaje"}
