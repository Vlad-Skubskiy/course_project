from pydantic import BaseModel
from datetime import datetime
from typing import Optional


# Клас для отримання нових сканувань від ESP32
class ScanRequest(BaseModel):
    nfc_uuid: str
    device_id: str


# НОВИЙ КЛАС: Клас для оновлення інформації про таблетки з фронтенду
class ScanUpdate(BaseModel):
    med_name: str
    remind_time: str  # Наприклад, "08:30"
    dosage: int


# Клас для відображення історії в таблиці
class ScanResponse(BaseModel):
    id: int
    nfc_uuid: str
    device_id: str
    timestamp: datetime
    med_name: Optional[str] = None
    remind_time: Optional[str] = None
    dosage: Optional[int] = 1

    class Config:
        from_attributes = True
