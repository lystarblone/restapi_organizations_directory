from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, JSON
from sqlalchemy.orm import relationship
from app.database import Base

organization_activity = Table(
    "organization_activity",
    Base.metadata,
    Column("organization_id", Integer, ForeignKey("organizations.id"), primary_key=True),
    Column("activity_id", Integer, ForeignKey("activities.id"), primary_key=True),
)

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    organizations = relationship("Organization", back_populates="building")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True)

    parent_id = Column(Integer, ForeignKey("activities.id"))
    parent = relationship("Activity", remote_side=[id], back_populates="children")
    children = relationship("Activity", back_populates="parent")

    organizations = relationship(
        "Organization", secondary=organization_activity, back_populates="activities"
    )

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)

    phone_numbers = Column(JSON, default=list, nullable=False)

    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    building = relationship("Building", back_populates="organizations")

    activities = relationship(
        "Activity", secondary=organization_activity, back_populates="organizations"
    )