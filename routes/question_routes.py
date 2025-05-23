from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
from database import db
from models.question_model import Question, Answer, LikeDislikeRequest
from typing import List
from datetime import datetime
import requests
from bson import ObjectId
import re
from together import Together

router = APIRouter()

@router.get("/questions")
def get_all_questions():
    questions = list(db.Questions.find())

    if not questions:
        return JSONResponse(status_code=200, content={"message": "No se encontraron preguntas.", "questions": 0})

    for question in questions:
        question["_id"] = str(question["_id"])
        
        user = db.Users.find_one({"_id": ObjectId(question["userId"])}, {"fullname": 1, "activeQuestions": 1, "answeredQuestions": 1, "imgBase64": 1})
        user["_id"] = str(user["_id"])
        question["user"] = user if user else {}

        if "date" in question and isinstance(question["date"], datetime):
            question["date"] = question["date"].isoformat()

        question["answersCount"] = len(question.get("answers", []))
        question.pop("answers", None)

    return JSONResponse(
        status_code=200,
        content={"message": "Preguntas obtenidas exitosamente.", "questions": questions}
    )
    
    
@router.get("/basic_list_questions")
def get_all_questions():
    questions = db.Questions.find({}, {"_id": 1, "title": 1})
    questions_list = [{"_id": str(q["_id"]), "title": q["title"]} for q in questions]

    if not questions_list:
        return JSONResponse(status_code=404, content={"message": "No se encontraron preguntas."})

    return JSONResponse(
        status_code=200,
        content={"message": "Preguntas obtenidas exitosamente.", "questions": questions_list}
    )


@router.put("/questions/{question_id}")
def update_question(question_id: str, data: dict = Body(...)):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID de pregunta inválido")

    existing = db.Questions.find_one({"_id": ObjectId(question_id)})
    if not existing:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    db.Questions.update_one(
        {"_id": ObjectId(question_id)},
        {"$set": data}
    )

    updated_question = db.Questions.find_one({"_id": ObjectId(question_id)})
    updated_question["_id"] = str(updated_question["_id"])

    return {
        "message": "Pregunta actualizada correctamente",
        "question": updated_question
    }


@router.delete("/questions/{question_id}")
def delete_question(question_id: str):
    if not ObjectId.is_valid(question_id):
        raise HTTPException(status_code=400, detail="ID de pregunta inválido")

    question = db.Questions.find_one({"_id": ObjectId(question_id)})
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    db.Questions.delete_one({"_id": ObjectId(question_id)})

    return {"message": "Pregunta eliminada correctamente"}

    
@router.post("/add_question")
def add_question(question: Question):
    user = db.Users.find_one({"_id": ObjectId(question.userId)})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    new_question = {
        "userId": question.userId,
        "title": question.title,
        "textContent": question.textContent,
        "viewsCount": 0,
        "answersCount": 0,
        "date": question.date.isoformat(),
        "tags": question.tags,
        "answers": []
    }

    inserted_question = db.Questions.insert_one(new_question)
    question_id_str = str(inserted_question.inserted_id)

    db.Users.update_one(
        {"_id": ObjectId(question.userId)},
        {"$push": {"activeQuestions": question_id_str}}
    )
    
    new_question["_id"] = str(inserted_question.inserted_id)

    return JSONResponse(
        status_code=201,
        content={"message": "Pregunta agregada exitosamente.", "question": new_question}
    )
    
    
@router.get("/questions/{question_id}")
def get_question_by_id(question_id: str):
    obj_id = ObjectId(question_id)

    question = db.Questions.find_one_and_update(
        {"_id": obj_id},
        {"$inc": {"viewsCount": 1}},
        return_document=True
    )

    if not question:
        return JSONResponse(status_code=404, content={"message": f"No se encontró la pregunta con el ID {question_id}."})

    question["_id"] = str(question["_id"])
    question["userId"] = str(question["userId"])

    user = db.Users.find_one(
        {"_id": ObjectId(question["userId"])},
        {"fullname": 1, "activeQuestions": 1, "answeredQuestions": 1, "imgBase64": 1}
    )

    if user:
        user["_id"] = str(user["_id"])
        question["user"] = user
    else:
        question["user"] = {}

    if "date" in question and isinstance(question["date"], datetime):
        question["date"] = question["date"].isoformat()

    if "answers" in question and isinstance(question["answers"], list):
        for ans in question["answers"]:
            user = db.Users.find_one(
                {"_id": ObjectId(ans["userId"])},
                {"fullname": 1, "answeredQuestions": 1, "imgBase64": 1}
            )
            
            user["_id"] = str(user["_id"])
            ans["user"] = user
            
            if "userId" in ans:
                ans["userId"] = str(ans["userId"])
            if "date" in ans and isinstance(ans["date"], datetime):
                ans["date"] = ans["date"].isoformat()

    return JSONResponse(
        status_code=200,
        content={"message": "Detalle de la pregunta obtenido exitosamente.", "question": question}
    )
    

@router.put("/questions/add_answer/{question_id}")
def add_answer_to_question(question_id: str, answer: Answer):
    question = db.Questions.find_one({"_id": ObjectId(question_id)})

    if not question:
        return JSONResponse(
            status_code=404,
            content={"message": "Pregunta no encontrada."}
        )
    
    db.Users.update_one(
        {"_id": ObjectId(answer.userId)},
        {"$push": {"answeredQuestions": question_id}}
    )

    new_answer = answer.dict()
    db.Questions.update_one(
        {"_id": ObjectId(question_id)},
        {"$push": {"answers": new_answer}, "$inc": {"answersCount": 1}}
    )

    return JSONResponse(
        status_code=200,
        content={"message": "Respuesta agregada correctamente."}
    )
    
    
@router.post("/questions/answer/likeordeslike")
def add_like_or_dislike(data: LikeDislikeRequest):
    question = db.Questions.find_one({"_id": ObjectId(data.questionId)})

    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")

    answer = question["answers"][data.answerIndex]

    if data.userId in answer.get("listLike", []) or data.userId in answer.get("listDeslike", []):
        return {"message": "El usuario ya ha votado en esta respuesta"}

    update_query = {}
    if data.action == "like":
        update_query = {
            "$inc": {"answers.{0}.likes".format(data.answerIndex): 1},
            "$push": {"answers.{0}.listLike".format(data.answerIndex): data.userId}
        }
    elif data.action == "dislike":
        update_query = {
            "$inc": {"answers.{0}.dislikes".format(data.answerIndex): 1},
            "$push": {"answers.{0}.listDeslike".format(data.answerIndex): data.userId}
        }
    else:
        raise HTTPException(status_code=400, detail="Acción inválida")

    db.Questions.update_one({"_id": ObjectId(data.questionId)}, update_query)

    return {"message": f"{data.action} agregado correctamente"}


@router.post("/ask_ia")
async def ask_ai(data: dict):
    API_KEY = "3b69763e9912d7a4bbe2595ad7bfdb9080123b95c6560f6480aaef2d4dfc1fb4"
    question = data.get("question", "")

    if not question:
        return {"error": "No se proporcionó ninguna pregunta"}

    client = Together(api_key=API_KEY)

    prompt = (
        "Responde de manera técnica y concisa en español. "
        "La respuesta debe tener menos de 500 palabras. Si se trata de código hasta 1000 máximo. "
        "La respuesta no debe tener explicaciones del pensamiento que tienes al resolver la duda. "
        "Todas las líneas de texto de la respuesta no deben tener espacios en blanco al inicio, no importa si están bajo indentación de una lista ni nada. "
        "Para formatear la respuesta correctamente en Markdown, sigue estrictamente estas reglas:\n\n"
        "- Usa *negrita* para destacar palabras o frases clave.\n"
        "- Usa **mini títulos** para destacar mini títulos.\n"
        "- Usa _cursiva_ para enfatizar términos importantes.\n"
        "- Usa [texto](url) para incluir enlaces.\n"
        "- Usa > al inicio para citas o comentarios importantes.\n"
        "- Usa - al inicio para listas.\n"
        "- Para código, usa exactamente este formato sin omitir líneas:\n\n"
        "```\n"
        "[código aquí]\n"
        "```\n"
        "- No dejes bloques de código abiertos. Cada bloque debe cerrarse con ```.\n\n"
        f"Pregunta: {question}\n\n"
    )

    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        raw_answer = response.choices[0].message.content.strip()
        clean_answer = re.sub(r"<think>.*?</think>", "", raw_answer, flags=re.DOTALL).strip()
        return {"answer": clean_answer}
    except Exception as e:
        return {"error": str(e)}