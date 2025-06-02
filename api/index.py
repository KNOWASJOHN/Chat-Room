from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from typing import List, Optional
import uuid
from datetime import datetime

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (in production, use a database like Supabase)
rooms = {}
messages = {}

class RoomCreate(BaseModel):
    nickname: str

class RoomJoin(BaseModel):
    nickname: str
    room_code: str

class MessageSend(BaseModel):
    room_code: str
    nickname: str
    message: str

@app.get("/")
async def root():
    return {"message": "Chat API is running"}

@app.post("/api/create-room")
async def create_room(data: RoomCreate):
    import random
    room_code = str(random.randint(10000000, 99999999))
    while room_code in rooms:
        room_code = str(random.randint(10000000, 99999999))
    
    rooms[room_code] = {
        "users": [data.nickname],
        "created_at": datetime.now().isoformat()
    }
    messages[room_code] = []
    
    return {"room_code": room_code, "success": True}

@app.post("/api/join-room")
async def join_room(data: RoomJoin):
    if data.room_code not in rooms:
        return {"success": False, "error": "Room does not exist"}
    
    if data.nickname in rooms[data.room_code]["users"]:
        return {"success": False, "error": "Nickname already in use"}
    
    rooms[data.room_code]["users"].append(data.nickname)
    return {"success": True, "users": rooms[data.room_code]["users"]}

@app.post("/api/send-message")
async def send_message(data: MessageSend):
    if data.room_code not in rooms:
        return {"success": False, "error": "Room does not exist"}
    
    message = {
        "id": str(uuid.uuid4()),
        "nickname": data.nickname,
        "message": data.message,
        "timestamp": datetime.now().isoformat()
    }
    
    messages[data.room_code].append(message)
    
    # Keep only last 100 messages
    if len(messages[data.room_code]) > 100:
        messages[data.room_code] = messages[data.room_code][-100:]
    
    return {"success": True, "message": message}

@app.get("/api/messages/{room_code}")
async def get_messages(room_code: str):
    if room_code not in rooms:
        return {"success": False, "error": "Room does not exist"}
    
    return {
        "success": True, 
        "messages": messages.get(room_code, []),
        "users": rooms[room_code]["users"]
    }

@app.get("/api/room/{room_code}/users")
async def get_room_users(room_code: str):
    if room_code not in rooms:
        return {"success": False, "error": "Room does not exist"}
    
    return {"success": True, "users": rooms[room_code]["users"]}

# For Vercel deployment
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
