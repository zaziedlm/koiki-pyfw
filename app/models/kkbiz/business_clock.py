from sqlalchemy import CheckConstraint, Column, Date, Integer, String, Text, Time

from libkoiki.db.base import Base


class BusinessClock(Base):
    """
    Business clock singleton row controlling visible time behaviour.
    """

    __tablename__ = "business_clock"

    __table_args__ = (
        CheckConstraint("id = 1", name="ck_business_clock_singleton"),
    )

    mode = Column(String(16), nullable=False, default="REALTIME")
    base_timezone = Column(String(64), nullable=False, default="Asia/Tokyo")

    frozen_business_date = Column(Date, nullable=True)
    frozen_business_time = Column(Time, nullable=True)

    offset_days = Column(Integer, nullable=False, default=0)
    offset_minutes = Column(Integer, nullable=False, default=0)

    comment = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_by = Column(String(255), nullable=False, default="system")
