from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from core.database import Base


class AlertsSent(Base):
    __tablename__ = "alerts_sent"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    alert_type = Column(String(20), nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
