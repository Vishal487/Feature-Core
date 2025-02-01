from pydantic import BaseModel
from typing import List, Optional

class FeatureBase(BaseModel):
    name: str
    is_enabled: bool
    parent_id: Optional[int] = None

class FeatureCreate(FeatureBase):
    pass

class Feature(FeatureBase):
    id: int
    children: Optional[List["Feature"]] = []

    class Config:
        from_attributes = True

# For recursive relationships
Feature.update_forward_refs()

class AllFeaturesList(BaseModel):
    features: Optional[List["Feature"]] = []