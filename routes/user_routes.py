from fastapi import APIRouter, HTTPException
from database import db
from models.user_model import User
from models.forum_model import Forum
from models.resource_model import Resource
from models.question_model import Question
from models.user_model import UpdateUserModel
from models.user_model import LoginRequest
from models.user_model import UpdateEmailRequest
from models.user_model import UpdatePasswordRequest
from models.user_model import DeleteAccountRequest
from models.user_model import VerifyEmail
from typing import List
from passlib.context import CryptContext
from fastapi.responses import JSONResponse
from bson import ObjectId
from jwt_utils import crear_token
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register_user", response_model=User)
async def register_user(user: User):
    if db.Users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    user_dict = user.dict(exclude={"_id"})
    hashed_password = pwd_context.hash(user.password)
    user_dict["password"] = hashed_password

    result = db.Users.insert_one(user_dict)
    user_id = str(result.inserted_id)

    token = crear_token({"user_id": user_id, "email": user.email})

    db.Users.update_one({"_id": result.inserted_id}, {"$set": {"jwtoken": token}})
    user_dict["_id"] = user_id
    user_dict["jwtoken"] = token

    user_dict.pop("password", None)

    return {
        "message": "Usuario registrado exitosamente",
        "user": user_dict,
        "token": token
    }



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

    active_forums_raw = get_documents_by_ids("Forums", user.get("activeAllForums", []), {"_id": 1, "creator": 1, "title": 1, "activeUsers": 1, "messages": 1, "imgBase64": 1})
    active_forums = [
        {
            "_id": str(forum["_id"]),
            "imgBase64": forum.get("imgBase64", None),
            "creator": forum["creator"],
            "title": forum["title"],
            "usersCount": len(forum.get("activeUsers", [])),
            "messagesCount": len(forum.get("messages", [])),
        }
        for forum in active_forums_raw
    ]

    saved_projects = get_documents_by_ids("Projects", user.get("savedProjects", []))
    saved_resources = get_documents_by_ids("Resources", user.get("savedResources", []))
    created_resources = get_documents_by_ids("Resources", user.get("resourcesCreated", []))

    def convert_ids_to_str(documents):
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        return documents

    response_data = {
        "user": user,
        "activeQuestions": convert_ids_to_str(active_questions),
        "answeredQuestions": convert_ids_to_str(answered_questions),
        "activeForums": active_forums,
        "savedProjects": convert_ids_to_str(saved_projects),
        "savedResources": convert_ids_to_str(saved_resources),
        "createdResources": convert_ids_to_str(created_resources)
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
        token = crear_token({"user_id": user_data["_id"], "email": user_data["email"]})
        db.Users.update_one({"email": user.email}, {"$set": {"jwtoken": token}})
        user_data["jwtoken"] = token
        user_data["password"] = None
        
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
    
    if not user or not pwd_context.verify(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    user["_id"] = str(user["_id"])
    token = crear_token({"user_id": user["_id"], "email": user["email"]})

    db.Users.update_one({"_id": ObjectId(user["_id"])}, {"$set": {"jwtoken": token}})
    user["jwtoken"] = token

    return {
        "message": "Login exitoso",
        "user": user,
    }
    
@router.post("/update_user")
async def updateUser(user_data: UpdateUserModel):
    user = db.Users.find_one({"email": user_data.email})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not pwd_context.verify(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    update_fields = {
        "fullname": user_data.nombre,
        "phone": user_data.telefono,
        "country": user_data.pais,
    }

    if user_data.imgBase64:
        update_fields["imgBase64"] = user_data.imgBase64

    db.Users.update_one({"email": user_data.email}, {"$set": update_fields})

    updated_user = db.Users.find_one({"email": user_data.email})
    updated_user["_id"] = str(updated_user["_id"])

    return JSONResponse(
        status_code=200,
        content={"message": "Usuario actualizado con éxito", "user": updated_user}
    )
    
    
@router.post("/update_email")
async def update_email(request: UpdateEmailRequest):
    user = db.Users.find_one({"_id": ObjectId(request.user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not pwd_context.verify(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    if db.Users.find_one({"email": request.newEmail}):
        raise HTTPException(status_code=400, detail="El nuevo email ya está en uso")

    db.Users.update_one({"_id": ObjectId(request.user_id)}, {"$set": {"email": request.newEmail}})
    
    return JSONResponse(status_code=200, content={"message": "Email actualizado con éxito"})


@router.post("/update_password")
async def update_password(request: UpdatePasswordRequest):
    user = db.Users.find_one({"email": request.email})

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not pwd_context.verify(request.currentPassword, user["password"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    hashed_new_password = pwd_context.hash(request.newPassword)
    db.Users.update_one({"email": request.email}, {"$set": {"password": hashed_new_password}})

    return JSONResponse(status_code=200, content={"message": "Contraseña actualizada con éxito"})


@router.delete("/delete_account")
async def delete_account(request: DeleteAccountRequest):
    user = db.Users.find_one({"email": request.email})

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not pwd_context.verify(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    user_id = str(user["_id"])

    db.Users.delete_one({"_id": ObjectId(user["_id"])})

    db.Forums.update_many(
        {"activeUsers.userId": user_id},
        {"$pull": {"activeUsers": {"userId": user_id}}}
    )

    return JSONResponse(status_code=200, content={"message": "Cuenta eliminada con éxito"})