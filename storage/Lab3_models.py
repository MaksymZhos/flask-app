from sqlalchemy import Column, String, Float, Integer, DateTime
from datetime import datetime
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class DronePositionEvent(Base):
    __tablename__ = 'drone_position_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    drone_id = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    signal_strength = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    trace_id = Column(String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'drone_id': self.drone_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'signal_strength': self.signal_strength,
            'timestamp': self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'date_created': self.date_created.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'trace_id': self.trace_id
        }

class TargetAcquisitionEvent(Base):
    __tablename__ = 'target_acquisition_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    drone_id = Column(String(255), nullable=False)
    target_id = Column(String(255), nullable=False)
    acquisition_type = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=False)
    certainty = Column(Integer, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    date_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    trace_id = Column(String(255), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'drone_id': self.drone_id,
            'target_id': self.target_id,
            'acquisition_type': self.acquisition_type,
            'target_type': self.target_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'certainty': self.certainty,
            'timestamp': self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'date_created': self.date_created.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            'trace_id': self.trace_id
        }
