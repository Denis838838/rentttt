from sqlalchemy import Column, Integer, String, Text
from database import Base
import json

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    payment_day = Column(String, nullable=True)
    contract_end = Column(String, nullable=True)
    meetings = Column(Text, nullable=True, default="[]")
    meters = Column(Text, nullable=True, default="[]")
    payments = Column(Text, nullable=True, default="[]")

    def get_meetings(self):
        return json.loads(self.meetings)

    def get_meters(self):
        return json.loads(self.meters)

    def get_payments(self):
        return json.loads(self.payments)
