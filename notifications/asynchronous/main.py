import asyncio
import json
import random
from typing import Optional, List

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from starlette.websockets import WebSocket, WebSocketDisconnect

from notifications.asynchronous.db import crud_tasks, crud_users, database
from notifications.utils import generate_key

app = FastAPI()
WS_CLIENTS = {}  # {"user_id": "client_websocket"}


class WSConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def accept(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active_connections.remove(user_id)

    async def send_personal_message(self, user_id: str, message: str):
        websocket = self.active_connections.get(user_id)
        await websocket.send(message)


ws_manager = WSConnectionManager()


def get_ws_clients():
    return WS_CLIENTS


class Response(BaseModel):
    result: str


class LaunchTask(BaseModel):
    user_id: str
    sleep: Optional[int]


class Task(LaunchTask):
    task_id: str
    result: Optional[str]


class InUser(BaseModel):
    username: str


class OutUser(InUser):
    id: str
    username: str


@app.on_event('startup')
async def start():
    print("Started")
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    print("Finished")
    await database.disconnect()


@app.get('/')
async def root():
    messages = {"message": "This is root route."}
    return messages


@app.post('/user/create', response_model=OutUser)
async def create_user(user: InUser):
    id = generate_key()
    created = await crud_users.create(database, {'id': id, "username": user.username})

    return OutUser(id=id, username=user.username)


@app.post('/process', response_model=Response)
async def process(obj: LaunchTask, ws_clients=Depends(get_ws_clients)):
    processing_result_variants = [True, True, True, False, True, True, True, True, False, True]
    processing_result_gotten = random.choice(processing_result_variants)

    sleep_secs = obj.sleep if obj.sleep else 5
    await asyncio.sleep(sleep_secs)

    # TODO notify about 'processing' stop

    # store to db
    result_id = generate_key()
    await crud_tasks.create(database, {"id": result_id,
                                       "user_id": obj.user_id,
                                       "result": str(processing_result_gotten)})

    # TODO send notification
    print(ws_clients)
    if ws_clients.get(obj.user_id):
        ws_clients.get(obj.user_id).send_text(f"You result {result_id} is ready: {processing_result_gotten}")

    return Response(result='good')


@app.websocket('/ws/{user}')
async def notify(websocket: WebSocket, user: str):
    await ws_manager.accept(user, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            message_parsed = json.loads(message)
            print(message)
            action = message_parsed.get('action')
            if user and action == 'subscribe':

                print(f'connected: {websocket}')


    except WebSocketDisconnect:

        ws_manager.disconnect(websocket)

        await ws_manager.broadcast(f"Client #{user} left.")