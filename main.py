import os
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

app = FastAPI()

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date_visited = Column(DateTime, default=datetime.now)
    spot = Column(String)
    clicks = relationship("Click", back_populates="clicker")

class Click(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date_clicked = Column(DateTime, default=datetime.now)
    clicker_id = Column(Integer, ForeignKey("visits.id"))
    destination = Column(String)
    clicker = relationship("Visit", back_populates="clicks")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ClickCreate(BaseModel):
    clicker_id: int
    destination: str

class ClickResponse(BaseModel):
    id: int
    clicker_id: int
    destination: str
    date_clicked: datetime
    class Config:
        orm_mode = True

class VisitCreate(BaseModel):
    spot: str

class VisitResponse(BaseModel):
    id: int
    spot: str
    date_visited: datetime
    clicks: List[ClickResponse] = []
    class Config:
        orm_mode = True

@app.post("/visit/", response_model=VisitResponse)
async def new_visit(item: VisitCreate, db: Session = Depends(get_db)):
    db_item = Visit(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/visit/{visit_id}", response_model=VisitResponse)
async def read_visits(visit_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Visit).filter(Visit.id == visit_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.post("/click/", response_model=ClickResponse)
async def new_click(item: ClickCreate, db: Session = Depends(get_db)):
    db_item = Click(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/click/{click_id}", response_model=ClickResponse)
async def read_click(click_id: int, db: Session = Depends(get_db)):
    db_item = db.query(Click).filter(Click.id == click_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
