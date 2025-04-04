from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from database import db
from models.forum_model import Forum
from models.forum_model import Message
from models.forum_model import AddUserRequest
from typing import List
from datetime import datetime
from fastapi.responses import JSONResponse
from bson import ObjectId
router = APIRouter()
active_connections = {}

@router.get("/forum")
async def get_foros():
    forums = list(db.Forums.find())

    for foro in forums:
        foro["_id"] = str(foro["_id"])
        foro["creator"]["userId"] = str(foro["creator"]["userId"])
        foro["activeUsers"] = [{**user, "userId": str(user["userId"])} for user in foro["activeUsers"]]
        foro["messages"] = [{**msg, "userId": str(msg["userId"])} for msg in foro["messages"]]

    return forums


@router.get("/popular_forum")
async def get_popular_foros():
    forums = list(db.Forums.find())

    for foro in forums:
        statdistics = (len(foro["activeUsers"]) + len(foro["messages"])) / 2
        foro["statdistics"] = statdistics

        foro["_id"] = str(foro["_id"])
        foro["creator"]["userId"] = str(foro["creator"]["userId"])
        foro["activeUsers"] = [{**user, "userId": str(user["userId"])} for user in foro["activeUsers"]]
        foro["messages"] = [{**msg, "userId": str(msg["userId"])} for msg in foro["messages"]]

    sorted_forums = sorted(forums, key=lambda x: x["statdistics"], reverse=True)[:10]

    return sorted_forums


@router.post("/forum")
async def create_foro(foro: Forum):
    new_foro = foro.dict()
    new_foro["_id"] = str(db.Forums.insert_one(new_foro).inserted_id)
    
    db.Users.update_one(
        {"_id": ObjectId(foro.creator.userId)},
        {"$push": {
            "activeOwnForums": str(new_foro["_id"]),
            "activeAllForums": str(new_foro["_id"])
        }}
    )
    
    new_foro["creationDate"] = new_foro["creationDate"].isoformat()
    return JSONResponse(content={"message": "Foro creado con éxito", "foro": new_foro}, status_code=201)


@router.put("/forum/{forum_id}")
async def update_forum(forum_id: str, forum_data: dict):
    forum = db.Forums.find_one({"_id": ObjectId(forum_id)})

    if not forum:
        raise HTTPException(status_code=404, detail="Foro no encontrado")

    updated_data = {
        "title": forum_data.get("title", forum["title"]),
        "description": forum_data.get("description", forum["description"]),
        "imgBase64": forum_data.get("imgBase64", forum.get("imgBase64")),
    }

    db.Forums.update_one({"_id": ObjectId(forum_id)}, {"$set": updated_data})

    return JSONResponse(content={"message": "Foro actualizado con éxito"}, status_code=200)


@router.post("/forum/add_user")
async def add_user_to_forum(request: AddUserRequest):
    forum = db.Forums.find_one({"_id": ObjectId(request.forum_id)})

    if not forum:
        raise HTTPException(status_code=404, detail="Foro no encontrado")

    if any(user["userId"] == request.user.userId for user in forum["activeUsers"]):
        raise HTTPException(status_code=400, detail="El usuario ya pertenece al foro")

    db.Forums.update_one(
        {"_id": ObjectId(request.forum_id)},
        {"$push": {"activeUsers": request.user.dict()}}
    )
    
    db.Users.update_one(
        {"_id": ObjectId(request.user.userId)},
        {"$push": {"activeAllForums": str(forum["_id"])}}
    )

    return JSONResponse(
        status_code=200,
        content={"message": "Usuario agregado al foro exitosamente"}
    )
    

@router.post("/forum/remove_user")
async def remove_user_from_forum(request: AddUserRequest):
    forum = db.Forums.find_one({"_id": ObjectId(request.forum_id)})

    if not forum:
        raise HTTPException(status_code=404, detail="Foro no encontrado")

    if not any(user["userId"] == request.user.userId for user in forum["activeUsers"]):
        raise HTTPException(status_code=400, detail="El usuario no pertenece al foro")

    db.Forums.update_one(
        {"_id": ObjectId(request.forum_id)},
        {"$pull": {"activeUsers": {"userId": request.user.userId}}}
    )

    db.Users.update_one(
        {"_id": ObjectId(request.user.userId)},
        {"$pull": {"activeAllForums": str(forum["_id"])}}
    )

    return JSONResponse(
        status_code=200,
        content={"message": "Usuario eliminado del foro exitosamente"}
    )
    

@router.post("/forum/remove_forum")
async def remove_forum(request: AddUserRequest):
    forum = db.Forums.find_one({"_id": ObjectId(request.forum_id)})

    if not forum:
        raise HTTPException(status_code=404, detail="Foro no encontrado")

    if forum["creator"]["userId"] != request.user.userId:
        raise HTTPException(status_code=403, detail="Solo el creador puede eliminar el foro")

    db.Forums.delete_one({"_id": ObjectId(request.forum_id)})

    for user in forum.get("activeUsers", []):
        db.Users.update_one(
            {"_id": ObjectId(user["userId"])},
            {"$pull": {"activeAllForums": str(forum["_id"])}}
        )

    db.Users.update_one(
        {"_id": ObjectId(forum["creator"]["userId"])},
        {"$pull": {"activeOwnForums": str(forum["_id"])}}
    )

    return JSONResponse(
        status_code=200,
        content={"message": "Foro eliminado y usuarios actualizados exitosamente"}
    )
    

@router.websocket("/ws/{foro_id}")
async def websocket_endpoint(websocket: WebSocket, foro_id: str):
    await websocket.accept()

    if foro_id not in active_connections:
        active_connections[foro_id] = []
        
    active_connections[foro_id].append(websocket)

    foro = db.Forums.find_one({"_id": ObjectId(foro_id)}, {"messages": 1})
    messages = foro.get("messages", []) if foro else []
    
    for msg in messages:
        if isinstance(msg.get("date"), datetime):
            msg["date"] = msg["date"].isoformat()
                
    await websocket.send_json({"previous_messages": messages})

    try:
        while True:
            data = await websocket.receive_json()
            
            if "respondTo" in data and data["respondTo"] is not None:
                data["respondTo"]["userId"] = str(data["respondTo"]["userId"])

            message = Message(**data)
            message_data = message.dict()
            message_data["userId"] = str(message_data["userId"])

            if isinstance(message_data["date"], datetime):
                message_data["date"] = message_data["date"].isoformat()

            db.Forums.update_one(
                {"_id": ObjectId(foro_id)},
                {"$push": {"messages": message_data}}
            )

            for connection in active_connections[foro_id]:
                await connection.send_json(message_data)

    except WebSocketDisconnect:
        active_connections[foro_id].remove(websocket)
