from sqlalchemy import (Boolean, CheckConstraint, Column, ForeignKey, Integer,
                        String)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()  # Define Base here


class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    is_enabled = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey("feature_flags.id"), nullable=True)

    # Self-referential relationship
    children = relationship("FeatureFlag", back_populates="parent")
    parent = relationship("FeatureFlag", remote_side=[id], back_populates="children")

    # Add CHECK constraint
    __table_args__ = (CheckConstraint("parent_id != id", name="check_parent_not_self"),)
