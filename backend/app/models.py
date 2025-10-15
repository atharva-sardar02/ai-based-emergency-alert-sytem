"""SQLAlchemy ORM models for the emergency alert system."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Alert(Base):
    """Alert model storing normalized emergency alerts from all sources."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    natural_key = Column(String(255), unique=True, nullable=False, index=True)
    source = Column(String(100), nullable=False, index=True)
    provider_id = Column(String(255), nullable=True)
    
    # Core alert fields
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    event_type = Column(String(100), nullable=True)
    severity = Column(String(50), nullable=True)
    urgency = Column(String(50), nullable=True)
    area = Column(String(500), nullable=True)
    
    # Timestamps
    effective_at = Column(DateTime(timezone=True), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Provenance
    url = Column(Text, nullable=True)
    raw_payload = Column(Text, nullable=True)  # JSON string
    
    # Relationships
    classifications = relationship("Classification", back_populates="alert", cascade="all, delete-orphan")
    user_actions = relationship("UserAction", back_populates="alert", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_alerts_effective_at', 'effective_at'),
        Index('idx_alerts_source_provider', 'source', 'provider_id'),
    )


class Classification(Base):
    """LLM-generated classification for alerts."""
    
    __tablename__ = "classifications"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Classification output
    criticality = Column(String(20), nullable=False, index=True)  # High, Medium, Low
    rationale = Column(Text, nullable=True)
    model_version = Column(String(100), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    alert = relationship("Alert", back_populates="classifications")


class UserAction(Base):
    """User actions on alerts (acknowledge, mark irrelevant)."""
    
    __tablename__ = "user_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Action details
    action = Column(String(50), nullable=False)  # 'acknowledged' or 'irrelevant'
    note = Column(Text, nullable=True)
    actor = Column(String(255), nullable=True)  # Placeholder for future auth
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    alert = relationship("Alert", back_populates="user_actions")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_actions_alert_action', 'alert_id', 'action'),
    )

