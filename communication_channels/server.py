import asyncio
import json
import secrets
from typing import Callable

import websockets
from websockets.legacy.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK


from templates import MessagesTemplates

# TODO aiosqlite

CONNECTIONS = {} # {connection_id: websocket, ...}
ROOMS = {}  # {"room_id": (connection_id_1, connection_id_2, ...), "rood_id": (...), ...}
CONNECTIONS_IN_ROOMS = {}  # {connection_id: room_id, ...}


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
        if connection.id not in CONNECTIONS_IN_ROOMS.keys():
            await connection.send(message=MessagesTemplates['personally']['available_rooms']
                                  .format(rooms_list=list(ROOMS.keys())))
        else:
            websockets.broadcast(websockets=ROOMS[CONNECTIONS_IN_ROOMS[connection.id]],
                                 message=MessagesTemplates['selective']['message_to_room']
                                 .format(message=json.dumps(data['message']), connection_id=connection.id))


class RoomsManager:

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

        websockets.broadcast(websockets=CONNECTIONS.values(),
                             message=MessagesTemplates['to_all']['new_room_created']
                             .format(new_room_id=new_room_id))

        await connection.send(message=MessagesTemplates['personally']['available_rooms']
                              .format(rooms_list=list(ROOMS.keys())))

    async def join_room(self, connection, data):
        ROOMS[data['id']].add(connection)
        CONNECTIONS_IN_ROOMS[connection.id] = data['id']
        await asyncio.sleep(0)

        websockets.broadcast(websockets=ROOMS[data['id']],
                             message=MessagesTemplates['selective']['new_room_member']
                             .format(connection_id=connection.id))

    async def leave_room(self, connection, data):
        room_id = CONNECTIONS_IN_ROOMS[connection.id]
        websockets.broadcast(websockets=ROOMS[room_id],
                             message=MessagesTemplates['selective']['left_room']
                             .format(connection_id=connection.id))

        ROOMS[room_id].remove(connection)
        CONNECTIONS_IN_ROOMS.pop(connection.id)


event_manager = EventManager(RoomsManager(), MessagesManager())


async def handler(websocket: WebSocketServerProtocol):
    print(f"New Connection detected: {websocket.id}")
    CONNECTIONS[websocket.id] = websocket

    await websocket.send(message=MessagesTemplates['personally']['connected'])

    await websocket.send(message=MessagesTemplates['personally']['available_rooms']
                         .format(rooms_list=list(ROOMS.keys())))

    try:
        while True:
            event = await websocket.recv()

            event = json.loads(event)
            await asyncio.sleep(0)

            await event_manager.get_handler(event['event'])(connection=websocket, data=event['data'])

    except ConnectionClosedOK as disconnected:
        CONNECTIONS.pop(websocket.id)


async def main():
    # handler is a coroutine that manages a connection.
    # When a client connects, websockets calls handler with the connection in argument.
    # When handler terminates, websockets closes the connection.
    async with websockets.serve(handler, "", 8088):
        await asyncio.Future()  # run forever ?


if __name__ == '__main__':
    asyncio.run(main())
