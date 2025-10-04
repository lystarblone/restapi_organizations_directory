import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

import math
import uvicorn
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import func, literal
from dotenv import load_dotenv
from app.database import SessionLocal, get_db
from app.models import Building, Activity, Organization, organization_activity
from app.schemas import BuildingOut, OrganizationOut, ActivityOut, RadiusSearch

load_dotenv()
app = FastAPI(title="Organization Directory API", description="REST API для справочника организаций, зданий и деятельностей", version="1.0.0")
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(x_api_key: str = Depends(api_key_header)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

@app.get("/organizations/by-building/{building_id}", response_model=List[OrganizationOut], dependencies=[Depends(verify_api_key)])
async def get_organizations_by_building(building_id: int, db: Session = Depends(get_db)):
    """Получить список организаций по ID здания.
    
    Args:
        building_id (int): Уникальный идентификатор здания.
    
    Returns:
        List[OrganizationOut]: Список организаций, расположенных в указанном здании.
    
    Raises:
        HTTPException 404: Если организации не найдены.
    """
    organizations = db.query(Organization).filter(Organization.building_id == building_id).all()
    if not organizations:
        raise HTTPException(status_code=404, detail="No organizations found for this building")
    return organizations

@app.get("/organizations/by-activity/{activity_id}", response_model=List[OrganizationOut], dependencies=[Depends(verify_api_key)])
async def get_organizations_by_activity(activity_id: int, db: Session = Depends(get_db)):
    """Получить список организаций по ID деятельности.
    
    Args:
        activity_id (int): Уникальный идентификатор деятельности.
    
    Returns:
        List[OrganizationOut]: Список организаций, связанных с указанной деятельностью.
    
    Raises:
        HTTPException 404: Если организации не найдены.
    """
    organizations = db.query(Organization).join(organization_activity).filter(organization_activity.c.activity_id == activity_id).all()
    if not organizations:
        raise HTTPException(status_code=404, detail="No organizations found for this activity")
    return organizations

@app.post("/organizations/by-radius", response_model=List[OrganizationOut], dependencies=[Depends(verify_api_key)])
async def get_organizations_by_radius(search: RadiusSearch, db: Session = Depends(get_db)):
    """Получить список организаций в заданном радиусе от координат.
    
    Args:
        search (RadiusSearch): Объект с координатами и радиусом поиска.
    
    Returns:
        List[OrganizationOut]: Список организаций в указанном радиусе.
    
    Raises:
        HTTPException 404: Если организации не найдены.
    """
    buildings = db.query(Building).all()
    valid_buildings = [b for b in buildings if haversine(search.latitude, search.longitude, b.latitude, b.longitude) <= search.radius_km]
    building_ids = [b.id for b in valid_buildings]
    organizations = db.query(Organization).filter(Organization.building_id.in_(building_ids)).all()
    if not organizations:
        raise HTTPException(status_code=404, detail="No organizations found in the specified radius")
    return organizations

@app.get("/buildings", response_model=List[BuildingOut], dependencies=[Depends(verify_api_key)])
async def get_buildings(db: Session = Depends(get_db)):
    """Получить список всех зданий.
    
    Returns:
        List[BuildingOut]: Список всех зарегистрированных зданий.
    
    Raises:
        HTTPException 404: Если здания не найдены.
    """
    buildings = db.query(Building).all()
    if not buildings:
        raise HTTPException(status_code=404, detail="No buildings found")
    return buildings

@app.get("/organizations/{organization_id}", response_model=OrganizationOut, dependencies=[Depends(verify_api_key)])
async def get_organization_by_id(organization_id: int, db: Session = Depends(get_db)):
    """Получить информацию об организации по её ID.
    
    Args:
        organization_id (int): Уникальный идентификатор организации.
    
    Returns:
        OrganizationOut: Детали организации.
    
    Raises:
        HTTPException 404: Если организация не найдена.
    """
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

@app.get("/organizations/by-activity-name/{activity_name}", response_model=List[OrganizationOut], dependencies=[Depends(verify_api_key)])
async def get_organizations_by_activity_name(activity_name: str, db: Session = Depends(get_db)):
    """Получить список организаций по названию деятельности (включая поддеятельности).
    
    Args:
        activity_name (str): Название корневой деятельности.
    
    Returns:
        List[OrganizationOut]: Список организаций, связанных с данной деятельностью и её поддеятельностями.
    
    Raises:
        HTTPException 404: Если деятельность или организации не найдены.
    """
    root_activity = db.query(Activity).filter(Activity.name == activity_name).first()
    if not root_activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    cte = db.query(Activity.id, literal(0).label("depth")).filter(Activity.id == root_activity.id).cte(name="activity_hierarchy", recursive=True)
    cte = cte.union_all(db.query(Activity.id, (cte.c.depth + 1).label("depth")).filter(Activity.parent_id == cte.c.id).filter(cte.c.depth < 2))
    activity_ids = [row[0] for row in db.query(cte.c.id).all()]
    organizations = db.query(Organization).join(organization_activity).filter(organization_activity.c.activity_id.in_(activity_ids)).distinct().all()
    if not organizations:
        raise HTTPException(status_code=404, detail="No organizations found for this activity tree")
    return organizations

@app.get("/organizations/by-name/{name}", response_model=List[OrganizationOut], dependencies=[Depends(verify_api_key)])
async def get_organizations_by_name(name: str, db: Session = Depends(get_db)):
    """Получить список организаций по частичному совпадению имени.
    
    Args:
        name (str): Часть названия организации для поиска.
    
    Returns:
        List[OrganizationOut]: Список организаций, чьи названия содержат указанную строку.
    
    Raises:
        HTTPException 404: Если организации не найдены.
    """
    organizations = db.query(Organization).filter(Organization.name.ilike(f"%{name}%")).all()
    if not organizations:
        raise HTTPException(status_code=404, detail="No organizations found with this name")
    return organizations

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)