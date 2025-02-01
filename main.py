import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Читаем URL базы данных из переменной окружения
# Railway обычно предоставляет переменную DATABASE_URL (например, postgresql://user:password@host:port/dbname)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost/dbname")

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL)

# Создаем сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс моделей
Base = declarative_base()

# Пример модели: Item
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

# Создаем таблицы, если их еще нет
Base.metadata.create_all(bind=engine)

# Pydantic-модель для ответа (можно расширять)
class ItemResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

# Инициализируем FastAPI
app = FastAPI()

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт для создания нового элемента
@app.post("/items/", response_model=ItemResponse)
def create_item(name: str, db: Session = Depends(get_db)):
    db_item = Item(name=name)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Эндпоинт для получения элемента по id
@app.get("/items/{item_id}", response_model=ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# Дополнительный эндпоинт для получения всех элементов
@app.get("/items/", response_model=list[ItemResponse])
def read_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return items