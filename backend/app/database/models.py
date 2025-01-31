from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    is_enabled = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("feature_flags.id"), nullable=True)

    # Self-referential relationship
    children = relationship("FeatureFlag", back_populates="parent")
    parent = relationship("FeatureFlag", remote_side=[id], back_populates="children")