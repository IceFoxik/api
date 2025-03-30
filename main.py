from fastapi import FastAPI, HTTPException
from contextlib import closing
from db import get_db_connection
from model import WorkerFactory
app = FastAPI()

@app.get("/worker/{worker_name}")
async def get_worker(worker_name: str):
    # Получаем соединение с базой данных
    with closing(get_db_connection()) as conn:
        # Ищем работника через фабрику
        worker = WorkerFactory.get_worker_by_surname(worker_name, conn)

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    return {
        "id": worker.id,
        "service_id": worker.service_id,
        "surname": worker.surname,
        "special_code": worker.special_code,
        "age": worker.age,
        "specialization": worker.specialization,
        "experience": worker.experience
    }