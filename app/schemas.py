from pydantic import BaseModel, Field
from typing import List, Optional

class BuildingBase(BaseModel):
    address: str = Field(..., description="Адрес здания")
    latitude: float = Field(..., description="Широта")
    longitude: float = Field(..., description="Долгота")

class BuildingOut(BuildingBase):
    id: int = Field(..., description="ID здания")

    class Config:
        from_attributes = True

class ActivityBase(BaseModel):
    name: str = Field(..., description="Название деятельности")

class ActivityOut(ActivityBase):
    id: int = Field(..., description="ID деятельности")
    parent_id: Optional[int] = Field(None, description="ID родительской деятельности")
    children: List["ActivityOut"] = Field(default_factory=list, description="Поддеятельности (до 3 уровней)")

    class Config:
        from_attributes = True

class OrganizationBase(BaseModel):
    name: str = Field(..., description="Название организации")
    phone_numbers: List[str] = Field(default_factory=list, description="Список номеров телефонов")

class OrganizationOut(OrganizationBase):
    id: int = Field(..., description="ID организации")
    building: BuildingOut = Field(..., description="Здание организации")
    activities: List[ActivityOut] = Field(default_factory=list, description="Список деятельностей")

    class Config:
        from_attributes = True

class RadiusSearch(BaseModel):
    latitude: float = Field(..., description="Широта центра")
    longitude: float = Field(..., description="Долгота центра")
    radius_km: float = Field(..., gt=0, description="Радиус в километрах")

ActivityOut.model_rebuild()