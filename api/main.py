from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import socketio
import random

# Initialize FastAPI and Socket.IO
app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi')

# Serve static files (HTML, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for rooms and user mappings
rooms = {}  # key: room_code, value: list of (sid, nickname)
user_rooms = {}  # key: sid, value: room_code

# Generate a unique 8-digit room code
def generate_room_code():
    while True:
        code = str(random.randint(10000000, 99999999))
        if code not in rooms:
            return code

# Serve the homepage
@app.get("/", response_class=HTMLResponse)
async def homepage():
    with open("static/index.html") as f:
        return f.read()

# Handle room creation
@sio.on('create_room')
async def create_room(sid, data):
    nickname = data.get('nickname', '').strip()
    if not nickname:
        await sio.emit('error', {'message': 'Nickname is required'}, to=sid)
        return
    room_code = generate_room_code()
    rooms[room_code] = [(sid, nickname)]
    user_rooms[sid] = room_code
    await sio.emit('room_created', {'room_code': room_code}, to=sid)

# Handle room joining
@sio.on('join_room')
async def join_room(sid, data):
    nickname = data.get('nickname', '').strip()
    room_code = data.get('room_code', '').strip()
    if not nickname or not room_code:
        await sio.emit('error', {'message': 'Nickname and room code are required'}, to=sid)
        return
    if room_code not in rooms:
        await sio.emit('error', {'message': 'Room does not exist'}, to=sid)
        return
    # Check for duplicate nickname
    if any(nick == nickname for _, nick in rooms[room_code]):
        await sio.emit('error', {'message': 'Nickname already in use'}, to=sid)
        return
    rooms[room_code].append((sid, nickname))
    user_rooms[sid] = room_code
    await sio.emit('room_joined', {'room_code': room_code}, to=sid)
    await sio.emit('user_joined', {'nickname': nickname}, room=room_code)
    user_list = [nick for _, nick in rooms[room_code]]
    await sio.emit('user_list', {'users': user_list}, room=room_code)

# Handle sending messages
@sio.on('send_message')
async def send_message(sid, data):
    room_code = user_rooms.get(sid)
    if room_code and data.get('message'):
        nickname = next(nick for s, nick in rooms[room_code] if s == sid)
        message = data['message'].strip()
        await sio.emit('new_message', {'nickname': nickname, 'message': message}, room=room_code)

# Handle user disconnection
@sio.on('disconnect')
async def disconnect(sid):
    if sid in user_rooms:
        room_code = user_rooms[sid]
        nickname = next(nick for s, nick in rooms[room_code] if s == sid)
        rooms[room_code] = [(s, n) for s, n in rooms[room_code] if s != sid]
        del user_rooms[sid]
        if rooms[room_code]:
            await sio.emit('user_left', {'nickname': nickname}, room=room_code)
            user_list = [n for _, n in rooms[room_code]]
            await sio.emit('user_list', {'users': user_list}, room=room_code)
        if not rooms[room_code]:
            del rooms[room_code]

# Create the Socket.IO ASGI app
sio_app = socketio.ASGIApp(sio, app)

# Run the app with Uvicorn when executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(sio_app, host="localhost", port=8000)
