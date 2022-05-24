import asyncio
import random
from typing import Optional

from fastapi import FastAPI, Depends
from pydantic import BaseModel
from starlette.websockets import WebSocket

from notifications.asynchronous.db import crud_tasks,crud_users, database
from notifications.utils import generate_key

app = FastAPI()
WS_CLIENTS = {}  # {"user_id": "client_websocket"}


def get_ws_clients():
    return WS_CLIENTS


class Response(BaseModel):
    result: str


class LaunchTask(BaseModel):
    user_id: int
    sleep: Optional[int]


class Task(LaunchTask):
    task_id: str
    result: Optional[str]


class InUser(BaseModel):
    username: str


class OutUser(InUser):
    id: str


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


@app.post('/user/create', response_model=Response)
async def create_user(user: InUser):
    await crud_users.create(database, {'id': generate_key(), "username": user.username})


@app.post('/process', response_model=Response)
async def process(obj: LaunchTask, ws_clients = Depends(get_ws_clients)):
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
    if ws_clients.get(obj.user_id):
        ws_clients.get(obj.user_id).send_text(f"You result {result_id} is ready: {processing_result_gotten}")

    return Response(result='good')


@app.websocket('/ws')
async def notify(websocket: WebSocket, ws_clients = Depends(get_ws_clients)):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            user_id = message.get('user_id')
            action = message.get('action')
            if user_id and action == 'subscribe':
                ws_clients[user_id] = websocket
    finally:
        ws_clients.remove(websocket)
