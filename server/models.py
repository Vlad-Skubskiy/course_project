from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from .database import Base


class MedScan(Base):
    __tablename__ = "med_scans"

    id = Column(Integer, primary_key=True, index=True)
    nfc_uuid = Column(String, index=True)
    device_id = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    med_name = Column(String, nullable=True)  # Назва пігулок
    remind_time = Column(String, nullable=True)  # Час прийому (HH:MM)
    dosage = Column(Integer, default=1)
