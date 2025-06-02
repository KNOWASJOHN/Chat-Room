import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import socketio
import random

# Initialize FastAPI and Socket.IO with CORS for production
app = FastAPI()
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"  # Configure this properly for production
)

# Rest of your code remains the same...

# Update the final section for production:
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(sio_app, host="localhost", port=port)
