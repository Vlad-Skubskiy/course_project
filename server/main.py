from fastapi import (
    FastAPI,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    Request,
    HTTPException,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from sqlalchemy.orm import Session
from . import models, schemas
from .database import SessionLocal, engine
from typing import List
import json
from server import schemas
from datetime import datetime

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


# Список активних підключень для WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ендпоінт для ESP32
@app.post("/api/scan")
async def process_scan(request: schemas.ScanRequest, db: Session = Depends(get_db)):
    db_scan = (
        db.query(models.MedScan)
        .filter(models.MedScan.nfc_uuid == request.nfc_uuid)
        .first()
    )

    if db_scan:
        # Важливо: якщо тег існує, ми все одно маємо сповістити фронтенд,
        # щоб він підсвітив цей рядок або відкрив модалку
        message = json.dumps(
            {
                "id": db_scan.id,
                "nfc_uuid": db_scan.nfc_uuid,
                "device_id": db_scan.device_id,
                "med_name": db_scan.med_name,
                "remind_time": db_scan.remind_time,
                "dosage": db_scan.dosage,
            }
        )
        await manager.broadcast(message)
        return {"status": "exists", "message": "Tag already registered"}

    new_scan = models.MedScan(
        nfc_uuid=request.nfc_uuid,
        device_id=request.device_id,
        timestamp=datetime.now(),
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)  # Обов'язково отримуємо ID, який згенерувала БД

    # ВИПРАВЛЕННЯ 1: Відправляємо повний об'єкт з ID
    message = json.dumps(
        {
            "id": new_scan.id,
            "nfc_uuid": new_scan.nfc_uuid,
            "device_id": new_scan.device_id,
            "timestamp": new_scan.timestamp.isoformat(),
        }
    )
    await manager.broadcast(message)


# WebSocket для додатка
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Просто тримаємо зв'язок
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    return db.query(models.MedScan).order_by(models.MedScan.timestamp.desc()).all()


@app.patch("/api/history/{item_id}")
async def update_scan(item_id: int, data: dict, db: Session = Depends(get_db)):
    # 1. Шукаємо запис у базі за ID
    scan = db.query(models.MedScan).filter(models.MedScan.id == item_id).first()

    if not scan:
        raise HTTPException(status_code=404, detail="Запис не знайдено")

    # 2. Оновлюємо поля (використовуємо get, щоб не впасти, якщо якогось поля немає)
    if "med_name" in data:
        scan.med_name = data["med_name"]
    if "remind_time" in data:
        scan.remind_time = data["remind_time"]
    if "dosage" in data:
        scan.dosage = data["dosage"]

    # 3. Зберігаємо зміни
    db.commit()
    db.refresh(scan)
    return scan
