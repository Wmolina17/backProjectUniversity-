from fastapi import APIRouter, HTTPException
from database import db
from models.user_model import User
from models.forum_model import Forum
from models.project_model import Project
from models.resource_model import Resource
from models.question_model import Question
from models.user_model import LoginRequest
from models.user_model import VerifyEmail
from typing import List
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from bson import ObjectId
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register_user", response_model=User)
async def register_user(user: User):
    if db.Users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    user_dict = user.dict(exclude={"_id"})
    hashed_password = pwd_context.hash(user.password)
    user_dict = user.dict(exclude={"password"})
    user_dict["password"] = hashed_password
    
    result = db.Users.insert_one(user_dict)

    if result.inserted_id:
        user_dict["_id"] = str(result.inserted_id)

        return JSONResponse(
            status_code=200,
            content={"message": "Usuario registrado exitosamente", "user": user_dict}
        )

    raise HTTPException(status_code=400, detail="Error al crear usuario")

@router.get("/profile/{id}", response_model=User)
async def get_user_profile(id: str):
    user = db.Users.find_one({"_id": ObjectId(id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user["_id"] = str(user["_id"])

    def get_documents_by_ids(collection, ids, projection=None):
        if not ids:
            return []
        query = {"_id": {"$in": [ObjectId(i) for i in ids]}}
        return list(db[collection].find(query, projection))

    active_questions = get_documents_by_ids("Questions", user.get("activeQuestions", []), {"_id": 1, "title": 1, "textContent": 1, "date": 1})
    answered_questions = get_documents_by_ids("Questions", user.get("answeredQuestions", []), {"_id": 1, "title": 1, "textContent": 1, "date": 1})
    active_forums = get_documents_by_ids("Forums", user.get("activeAllForums", []), {"_id": 1, "creator": 1, "title": 1, "usersCount": 1, "likeCount": 1})
    saved_projects = get_documents_by_ids("Projects", user.get("savedProjects", []))
    saved_resources = get_documents_by_ids("Resources", user.get("savedResources", []))

    def convert_ids_to_str(documents):
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        return documents

    response_data = {
        "user": user,
        "activeQuestions": convert_ids_to_str(active_questions),
        "answeredQuestions": convert_ids_to_str(answered_questions),
        "activeForums": convert_ids_to_str(active_forums),
        "savedProjects": convert_ids_to_str(saved_projects),
        "savedResources": convert_ids_to_str(saved_resources)
    }

    return JSONResponse(
        status_code=200,
        content={"message": "Perfil obtenido correctamente", "data": response_data}
    )

@router.post("/verify_user")
async def verify_if_user_exist(user: VerifyEmail):
    user_data = db.Users.find_one({"email": user.email})

    if user_data:
        user_data["_id"] = str(user_data["_id"])
        
        return JSONResponse(
            status_code=200,
            content={"exists": True, "user": user_data}
        )

    return JSONResponse(
        status_code=200,
        content={"exists": False, "user": None}
    )


@router.post("/login")
async def login(user_data: LoginRequest):
    user = db.Users.find_one({"email": user_data.email})
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if not pwd_context.verify(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    user["_id"] = str(user["_id"])

    return JSONResponse(
        status_code=200,
        content={"message": "Login exitoso", "user": user}
    )