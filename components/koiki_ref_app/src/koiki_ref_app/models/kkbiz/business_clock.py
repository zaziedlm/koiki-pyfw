from sqlalchemy import CheckConstraint, Column, Date, Integer, String, Text, Time, text

from libkoiki.db.base import Base


class BusinessClock(Base):
    """
    Business clock singleton row controlling visible time behaviour.
    """

    __tablename__ = "kkbiz_business_clock"

    __table_args__ = (
        CheckConstraint("id = 1", name="singleton"),
        CheckConstraint("version >= 1", name="positive_version"),
        CheckConstraint("mode IN ('REALTIME', 'OFFSET', 'FROZEN')", name="valid_mode"),
        CheckConstraint("(mode = 'FROZEN' AND frozen_business_date IS NOT NULL AND frozen_business_time IS NOT NULL) OR (mode != 'FROZEN' AND frozen_business_date IS NULL AND frozen_business_time IS NULL)", name="frozen_value_pair"),
    )

    mode = Column(String(16), nullable=False, default="REALTIME", server_default=text("'REALTIME'"))
    base_timezone = Column(String(64), nullable=False, default="Asia/Tokyo", server_default=text("'Asia/Tokyo'"))

    frozen_business_date = Column(Date, nullable=True)
    frozen_business_time = Column(Time, nullable=True)

    offset_days = Column(Integer, nullable=False, default=0, server_default=text("0"))
    offset_minutes = Column(Integer, nullable=False, default=0, server_default=text("0"))

    comment = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1, server_default=text("1"))
    updated_by = Column(String(255), nullable=False, default="system", server_default=text("'system'"))
