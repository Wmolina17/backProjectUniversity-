from fastapi import APIRouter, HTTPException
from database import db
from models.user_model import User
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