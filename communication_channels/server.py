import asyncio
import json
import sqlite3
from typing import Callable

import websockets
from websockets.legacy.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

from communication_channels.templates import MessagesTemplates
from communication_channels.utils import hash_password, check_password, generate_key
from models import database, crud_messages, crud_users, crud_rooms

CONNECTIONS = dict()  # {connection_id: {user: username, connection: connection}, ...}
CONNECTIONS_IN_ROOMS = dict()  # {room_id: (connection1, connection2, ...), ...}


class EventManager:

    def __init__(self, rooms_manager, messages_manager, auth_manager):
        self.rooms_manager = rooms_manager
        self.messages_manager = messages_manager
        self.auth_manager = auth_manager

        self.mapping = dict(**self.messages_manager.mapping,
                            **self.rooms_manager.mapping,
                            **self.auth_manager.mapping)

    def get_handler(self, event: str) -> Callable:
        return self.mapping.get(event)


class MessagesManager:

    @property
    def mapping(self):
        return {
            'message': self.message_handler
        }

    async def message_handler(self, connection, data):
        print(CONNECTIONS[connection.id]['username'])
        print(data['message'])

        user = await crud_users.get_by_username(database, CONNECTIONS[connection.id]['username'])
        room = await crud_rooms.get_by_name(database, data['room'])
        username = user[1]

        all_rooms = await crud_rooms.get_all(database)

        if connection not in CONNECTIONS_IN_ROOMS[data['room']]:
            await connection.send(message=MessagesTemplates['personally']['available_rooms']
                                  .format(rooms_list=[room[1] for room in all_rooms]))
        else:
            await crud_messages.create(database, {"id": generate_key(),
                                                  "user_id": user[0],
                                                  "room_id": room[0],
                                                  "text": data['message']})
            websockets.broadcast(websockets=CONNECTIONS_IN_ROOMS[data['room']],
                                 message=MessagesTemplates['selective']['message_to_room']
                                 .format(message=json.dumps(data['message']), connection_id=username))


class AuthManager:
    EVENTS = ('auth', 'register')

    @property
    def mapping(self):
        return {
            "auth": self.auth_handler,
            "register": self.register_handler,
        }

    async def auth_handler(self, connection, data):
        authenticated = False

        user_in_db = await crud_users.get_by_username(database, data['username'])

        if user_in_db and check_password(data['password'], user_in_db['password']):
            await connection.send(message=MessagesTemplates['personally']['successfully_auth'])
            authenticated = True

        else:
            await connection.send(message=MessagesTemplates['personally']['incorrect_credentials'])

        return authenticated

    async def register_handler(self, connection, data):
        registered = False
        user_in_db = await crud_users.get_by_username(database, data['username'])

        if user_in_db and check_password(data['password'], user_in_db['password']):
            await connection.send(
                message=MessagesTemplates['personally']['register_registered'].format(username=data['username']))
            registered = True
            return registered

        elif not user_in_db:
            try:
                res = await crud_users.create(database, {"id": str(connection.id),
                                                         "username": data['username'],
                                                         "is_active": True,
                                                         "password": hash_password(data['password'])})
                registered = True if res else False

            except sqlite3.IntegrityError:
                await connection.send(message=MessagesTemplates['personally']['repeated_username'])
                registered = False

        return registered


class RoomsManager:

    @property
    def mapping(self):
        return {
            "create_room": self.create_room,
            "join_room": self.join_room,
            "leave_room": self.leave_room,
        }

    async def create_room(self, connection, data):
        new_room_id = generate_key()

        user = await crud_users.get_by_username(database, CONNECTIONS[connection.id]['username'])

        try:

            await crud_rooms.create(database, {"id": new_room_id, "name": data['name'], "creator": user['id']})

            all_rooms = await crud_rooms.get_all(database)

            websockets.broadcast(websockets=[conn['connection'] for conn in CONNECTIONS.values()],
                                 message=MessagesTemplates['to_all']['new_room_created']
                                 .format(new_room_name=data['name']))

            await connection.send(message=MessagesTemplates['personally']['available_rooms']
                                  .format(rooms_list=[room[1] for room in all_rooms]))

            CONNECTIONS_IN_ROOMS[data['name']] = set()

            print(CONNECTIONS_IN_ROOMS)
        except sqlite3.IntegrityError as e:
            await connection.send(message=MessagesTemplates['personally']['repeated_room_name'])

    async def join_room(self, connection, data):
        room_name = data['name']
        room = await crud_rooms.get_by_name(database, room_name)
        username = CONNECTIONS[connection.id]['username']
        user = await crud_users.get_by_username(database, username)

        if CONNECTIONS_IN_ROOMS.get(room_name) and connection in CONNECTIONS_IN_ROOMS[room_name]:

            await connection.send(message=MessagesTemplates['personally']['already_in_room'])

        else:
            if not CONNECTIONS_IN_ROOMS.get(room_name):
                CONNECTIONS_IN_ROOMS[room_name] = set()

            CONNECTIONS_IN_ROOMS[room_name].add(connection)

            await asyncio.sleep(0)

            last_messages = await crud_messages.get_paginated(database, room[0], 0, 5)
            for message in last_messages[-1::-1]:
                await connection.send(message=MessagesTemplates['selective']['message_to_room']
                                      .format(connection_id=message[6], message=message[3]))

            message = MessagesTemplates['selective']['new_room_member'].format(connection_id=username)
            websockets.broadcast(websockets=list(CONNECTIONS_IN_ROOMS[room_name]),
                                 message=message)
            await crud_messages.create(database, {"id": generate_key(),
                                                  "user_id": user[0],
                                                  "room_id": room[0],
                                                  "text": message})


        print(CONNECTIONS_IN_ROOMS)

    async def leave_room(self, connection, data):
        room_id = data['name']

        username = CONNECTIONS[connection.id]['username']

        if connection not in CONNECTIONS_IN_ROOMS[room_id]:
            await connection.send(message=MessagesTemplates['personally']['already_left_room'])
        else:

            websockets.broadcast(websockets=list(CONNECTIONS_IN_ROOMS[room_id]),
                                 message=MessagesTemplates['selective']['left_room']
                                 .format(connection_id=username))
            CONNECTIONS_IN_ROOMS[room_id].remove(connection)

        print(CONNECTIONS_IN_ROOMS)


event_manager = EventManager(RoomsManager(), MessagesManager(), AuthManager())


# users, rooms, messages, auth
async def handler(websocket: WebSocketServerProtocol):
    print(f"New Connection detected: {websocket.id}")
    authenticated_or_registered = False
    username = None

    await websocket.send(message=MessagesTemplates['personally']['register_or_auth'])

    while not authenticated_or_registered:
        event = await websocket.recv()

        event = json.loads(event)
        await asyncio.sleep(0)

        if event['event'] in event_manager.auth_manager.EVENTS:
            authenticated_or_registered = await event_manager.get_handler(event['event'])(connection=websocket,
                                                                                          data=event['data'])
            username = event['data']["username"]
        else:
            await websocket.send(message=MessagesTemplates['personally']['register_or_auth'])

    CONNECTIONS[websocket.id] = {"connection": websocket, "username": username}

    await websocket.send(message=MessagesTemplates['personally']['connected'])

    available_rooms = await crud_rooms.get_all(database)
    print(available_rooms)
    await websocket.send(message=MessagesTemplates['personally']['available_rooms']
                         .format(rooms_list=[room[1] for room in available_rooms]))

    try:
        while True:
            event = await websocket.recv()

            event = json.loads(event)
            await asyncio.sleep(0)

            await event_manager.get_handler(event['event'])(connection=websocket, data=event['data'])

    except ConnectionClosedOK as disconnected:
        CONNECTIONS.pop(websocket.id)
        print(f"Connection ({websocket.id}) disconnected.")
        print(CONNECTIONS)


async def main():
    # handler is a coroutine that manages a connection.
    # When a client connects, websockets calls handler with the connection in argument.
    # When handler terminates, websockets closes the connection.
    await database.connect()
    async with websockets.serve(handler, "", 8088):
        await asyncio.Future()  # run forever ?

    await database.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
