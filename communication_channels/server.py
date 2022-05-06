import asyncio
import json
import secrets
from typing import Callable

import websockets
from websockets.legacy.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

# TODO aiosqlite

CONNECTIONS = {}
ROOMS = {}  # {"room_id": (connection_id_1, connection_id_2, ...), "rood_id": (...), ...}
CONNECTIONS_IN_ROOMS = {}


class EventManager:

    def __init__(self, rooms_manager, messages_manager):
        self.rooms_manager = rooms_manager
        self.messages_manager = messages_manager

        self.mapping = dict(**self.messages_manager.mapping,
                            **self.rooms_manager.mapping)

    def get_handler(self, event: str) -> Callable:
        return self.mapping.get(event)


class MessagesManager:

    @property
    def mapping(self):
        return {
            'message': self.message_handler
        }

    async def message_handler(self, connection, data):
        if connection.id  not in CONNECTIONS_IN_ROOMS.keys():
            await connection.send("Choose Room Before Creating Messages")
        else:
            websockets.broadcast(ROOMS[CONNECTIONS_IN_ROOMS[connection.id]],
                                 json.dumps(data['message']))
            await asyncio.sleep(0)


class RoomsManager:

    def __int__(self):
        self._connections = set()

        self.rooms = {}

    @property
    def mapping(self):
        return {
            "create_room": self.create_room,
            "join_room": self.join_room,
            "leave_room": self.leave_room,
        }

    def _create_room_id(self):
        return secrets.token_hex(nbytes=16)

    async def create_room(self, connection, data):
        new_room_id = self._create_room_id()
        ROOMS[new_room_id] = set()

        websockets.broadcast(CONNECTIONS.values(), f'New Room Created: {new_room_id}')
        await connection.send(f'Available rooms: {list(ROOMS.keys())}. Choose on of the rooms for further chatting.')

        return new_room_id

    async def join_room(self, connection, data):
        ROOMS[data['id']].add(connection)
        CONNECTIONS_IN_ROOMS[connection.id] = data['id']
        await asyncio.sleep(0)

        websockets.broadcast(ROOMS[data['id']], f"New Member ({connection.id}) in Room {data['id']}")
        return data['id']

    async def leave_room(self, connection, data):
        room_id = CONNECTIONS_IN_ROOMS[connection.id]
        websockets.broadcast(ROOMS[room_id], f"Member ({connection.id}) has left this room.")
        await asyncio.sleep(0)

        ROOMS[room_id].remove(connection)
        CONNECTIONS_IN_ROOMS.pop(connection.id)



        return room_id


event_manager = EventManager(RoomsManager(), MessagesManager())


async def handler(websocket: WebSocketServerProtocol):
    print(f"New Connection detected: {websocket.id}")
    CONNECTIONS[websocket.id] = websocket

    await websocket.send("You have connected.")

    await websocket.send(f'Available rooms: {list(ROOMS.keys())}. Choose on of the rooms for further chatting.')

    try:
        while True:
            event = await websocket.recv()

            event = json.loads(event)
            await asyncio.sleep(0)

            await event_manager.get_handler(event['event'])(connection=websocket, data=event['data'])

    except ConnectionClosedOK as disconnected:
        CONNECTIONS.pop(websocket.id)

        websockets.broadcast(CONNECTIONS.items(), f"Disconnected: {websocket.id}")

        print(f"Disconnected: {websocket.id}")

    finally:
        print("8")


async def main():
    async with websockets.serve(handler, "",
                                8088):  # handler is a coroutine that manages a connection. When a client connects, websockets calls handler with the connection in argument. When handler terminates, websockets closes the connection.
        await asyncio.Future()  # run forever ?


if __name__ == '__main__':
    asyncio.run(main())

# TODO different URIs
