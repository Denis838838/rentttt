import json
from sqlalchemy.orm import Session
from models import Tenant

def get_tenant(db: Session, tenant_id: int):
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()

def create_tenant(db: Session, tenant_id: int, name: str, payment_day: str, contract_end: str):
    tenant = Tenant(
        id=tenant_id,
        name=name,
        payment_day=payment_day,
        contract_end=contract_end,
        meetings=json.dumps([]),
        meters=json.dumps([]),
        payments=json.dumps([])
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

def delete_tenant(db: Session, tenant_id: int):
    tenant = get_tenant(db, tenant_id)
    if tenant:
        db.delete(tenant)
        db.commit()
        return True
    return False

def update_tenant_field(db: Session, tenant_id: int, field: str, value: str):
    tenant = get_tenant(db, tenant_id)
    if tenant:
        setattr(tenant, field, value)
        db.commit()
        db.refresh(tenant)
        return tenant
    return None
