from fastapi import FastAPI
import uvicorn
from core import db_manager

app = FastAPI()
@app.get("/")

def home():
    return {"message": "Server is running"}

@app.get("/events")
def get_events():
    events = db_manager.get_all_events()
    return {"events": events}