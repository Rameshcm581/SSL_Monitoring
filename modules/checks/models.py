from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class StatusChecks(Base):
    __tablename__ = "status_checks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    status = Column(String(10), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    http_status_code = Column(Integer, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
