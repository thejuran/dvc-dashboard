import enum
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.db.database import Base


class ReservationStatus(enum.StrEnum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    resort = Column(String, nullable=False)  # resort slug e.g. "polynesian"
    room_key = Column(String, nullable=False)  # composite key e.g. "deluxe_studio_lake"
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    points_cost = Column(Integer, nullable=False)  # total points for this reservation
    status = Column(String, nullable=False, default=ReservationStatus.CONFIRMED.value)
    confirmation_number = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contract = relationship("Contract", back_populates="reservations")
