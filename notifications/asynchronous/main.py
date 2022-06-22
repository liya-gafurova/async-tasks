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

# TODO что-то надо было сделать, но забыло, что именно
class WSConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def register(self, user_id: str, websocket: WebSocket):
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: Optional[str]):
        try:
            self.active_connections.remove(user_id)
        except Exception as er:
            print(er.args)

    async def send_personal_message(self, user_id: str, message: str):
        websocket = self.active_connections.get(user_id)
        await websocket.send_text(message)


ws_manager = WSConnectionManager()


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
async def process(obj: LaunchTask):
    processing_result_variants = [True, True, True, False, True, True, True, True, False, True]
    processing_result_gotten = random.choice(processing_result_variants)

    sleep_secs = obj.sleep if obj.sleep else 5
    await asyncio.sleep(sleep_secs)

    # store to db
    result_id = generate_key()
    created_mount = await crud_tasks.create(database, {"id": result_id,
                                       "user_id": obj.user_id,
                                       "result": str(processing_result_gotten)})

    # send notification
    if created_mount:
        await ws_manager.send_personal_message(obj.user_id, f"RESULT IS: {str(processing_result_gotten)}")

    return Response(result='good')


@app.websocket('/ws')
async def subscribe(websocket: WebSocket):

    await websocket.accept()
    print(f"new: {websocket}")

    user_id = None

    try:
        while True:
            message = await websocket.receive_json()
            print(message)
            user_id = message.get('user_id', None)
            action = message.get('action', None)
            print(f"{user_id} -- {action}")
            if user_id and action == 'subscribe':
                await ws_manager.register(user_id, websocket)
                print(ws_manager.active_connections)
            else:
                await websocket.send_text("enter user id to get subscribed")

    except WebSocketDisconnect as err:
        print(err)
        print(f"disconnected: {user_id}")
        ws_manager.disconnect(user_id)
        print(ws_manager.active_connections)
