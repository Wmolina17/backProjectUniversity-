from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Body
from database import db
from models.resource_model import Resource
from models.user_model import User
from bson import ObjectId

router = APIRouter()

@router.get("/resources")
async def get_resources():
    resources = list(db.Resources.find())
    for resource in resources:
        resource["_id"] = str(resource["_id"])
    return resources


@router.get("/resources/{user_id}")
async def get_resources_by_user(user_id: str):
    user = db.Users.find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    saved_ids = user.get("savedResources", [])
    created_ids = user.get("resourcesCreated", [])

    saved_object_ids = [ObjectId(res_id) for res_id in saved_ids if ObjectId.is_valid(res_id)]
    created_object_ids = [ObjectId(res_id) for res_id in created_ids if ObjectId.is_valid(res_id)]

    saved_resources = list(db.Resources.find({"_id": {"$in": saved_object_ids}}))
    created_resources = list(db.Resources.find({"_id": {"$in": created_object_ids}}))

    for resource in saved_resources + created_resources:
        resource["_id"] = str(resource["_id"])

    return {
        "savedResources": saved_resources,
        "createdResources": created_resources
    }
    
    
@router.put("/resources/{resource_id}")
async def update_resource(resource_id: str, data: dict = Body(...)):
    if not ObjectId.is_valid(resource_id):
        raise HTTPException(status_code=400, detail="ID de recurso inválido")

    existing = db.Resources.find_one({"_id": ObjectId(resource_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    update_result = db.Resources.update_one(
        {"_id": ObjectId(resource_id)},
        {"$set": data}
    )

    if update_result.modified_count == 0:
        return {"message": "No se realizaron cambios, el recurso ya estaba actualizado"}

    updated_resource = db.Resources.find_one({"_id": ObjectId(resource_id)})
    updated_resource["_id"] = str(updated_resource["_id"])

    return {"message": "Recurso actualizado correctamente", "resource": updated_resource}


@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: str):
    if not ObjectId.is_valid(resource_id):
        raise HTTPException(status_code=400, detail="ID de recurso inválido")

    result = db.Resources.delete_one({"_id": ObjectId(resource_id)})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurso no encontrado")

    return {"message": "Recurso eliminado correctamente"}


@router.post("/resources")
async def create_resource(resource: Resource):
    resource_dict = resource.dict()
    result = db.Resources.insert_one(resource_dict)
    resource_id = str(result.inserted_id)

    user_update = db.Users.update_one(
        {"_id": ObjectId(resource.userId)},
        {"$push": {"resourcesCreated": resource_id}}
    )

    if user_update.modified_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o no actualizado")

    resource_dict["_id"] = resource_id

    return {"message": "Resource created", "resource": resource_dict}


@router.put("/resources/save/{resource_id}/{user_id}")
async def save_resource(resource_id: str, user_id: str):
    resource = db.Resources.find_one({"_id": ObjectId(resource_id)})
    user = db.Users.find_one({"_id": ObjectId(user_id)})
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if resource_id not in user.get("savedResources", []):
        db.Users.update_one({"_id": ObjectId(user_id)}, {"$push": {"savedResources": resource_id}})
        db.Resources.update_one({"_id": ObjectId(resource_id)}, {"$inc": {"savedCount": 1}})
    
    return {"message": "Resource saved"}


@router.put("/resources/unsave/{resource_id}/{user_id}")
async def unsave_resource(resource_id: str, user_id: str):
    resource = db.Resources.find_one({"_id": ObjectId(resource_id)})
    user = db.Users.find_one({"_id": ObjectId(user_id)})
    
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if resource_id in user.get("savedResources", []):
        db.Users.update_one({"_id": ObjectId(user_id)}, {"$pull": {"savedResources": resource_id}})
        db.Resources.update_one({"_id": ObjectId(resource_id)}, {"$inc": {"savedCount": -1}})
    
    return {"message": "Resource unsaved"}


@router.put("/resources/{resource_id}/view")
async def add_view(resource_id: str):
    resource = db.Resources.find_one({"_id": ObjectId(resource_id)})
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    db.Resources.update_one({"_id": ObjectId(resource_id)}, {"$inc": {"viewsCount": 1}})
    return {"message": "View added"}
