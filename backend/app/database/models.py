from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()  # Define Base here

class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    is_enabled = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("feature_flags.id"), nullable=True)

    # Relationships
    children = relationship("FeatureFlag", back_populates="parent")
    parent = relationship("FeatureFlag", remote_side=[id], back_populates="children")