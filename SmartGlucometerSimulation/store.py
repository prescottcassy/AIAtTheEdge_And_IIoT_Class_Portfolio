"""
In-memory data store.
Replace with a real DB (SQLite / PostgreSQL via SQLAlchemy / SQLModel) for production.
"""
from typing import Dict, List
from models import Device, GlucoseReading, Alert


class Store:
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.readings: List[GlucoseReading] = []
        self.alerts: List[Alert] = []

    # Seed a couple of demo devices on startup
    def seed(self):
        from models import DeviceCreate
        for name, loc in [("GLU-001", "Ward A"), ("GLU-002", "Ward B"), ("GLU-003", "ICU")]:
            d = Device(name=name, location=loc)
            self.devices[d.id] = d


store = Store()
store.seed()
