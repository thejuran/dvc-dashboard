import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.db.database import Base


class PointAllocationType(enum.StrEnum):
    CURRENT = "current"  # current use year allocation
    BANKED = "banked"  # banked from prior use year
    BORROWED = "borrowed"  # borrowed from next use year
    HOLDING = "holding"  # holding account (late cancellation, etc.)


class PointBalance(Base):
    __tablename__ = "point_balances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    use_year = Column(Integer, nullable=False)  # the use year these points belong to (e.g. 2026)
    allocation_type = Column(String, nullable=False, default=PointAllocationType.CURRENT.value)
    points = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contract = relationship("Contract", back_populates="point_balances")
