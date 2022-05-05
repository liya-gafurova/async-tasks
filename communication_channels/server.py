import asyncio
import json
import secrets

import websockets
from websockets.legacy.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

# TODO aiosqlite

CONNECTIONS = set()
ROOMS = {}  # {"room_id": (connection_id_1, connection_id_2, ...), "rood_id": (...), ...}


class ARC:

    def __int__(self):
        self._connections = set()

        self.rooms = {}

    def _create_room_id(self):
        return secrets.token_hex(nbytes=16)

    def create_room(self, ):
        new_room_id = self._create_room_id()
        self.rooms[new_room_id] = set()

        return new_room_id

    def join_room(self, room_id, connection):
        self.rooms[room_id] = connection

        return self.rooms

    def leave_room(self, connection):
        pass


ChatManager = ARC()

async def async_iterator(iterable):
    for itm in iterable:
        yield itm
        await asyncio.sleep(0)





async def message_handler(ws, data):

    websockets.broadcast(ROOMS, json.dumps(data['message']))


async def create_room_handler(ws, data):
    created_room = ChatManager.create_room()
    await asyncio.sleep(0)

    websockets.broadcast(CONNECTIONS, f"New Room: {created_room}")


async def join_room_handler(ws, data):
    room_id = data['id']
    print(room_id)
    ROOMS[room_id].add(ws)
    await asyncio.sleep(0)

    websockets.broadcast(ROOMS[room_id], f"New Member: {ws.id}")


async def leave_room_handler(ws, data):
    room_id = data['id']
    ROOMS[room_id].remove(ws)
    await asyncio.sleep(0)

    websockets.broadcast(ROOMS[room_id], f"Disconnected Member: {ws.id}")


mapping = {
    'message': message_handler,
    "create_room": create_room_handler,
    "join_room": join_room_handler,
    "leave_room": leave_room_handler,
}


async def handler(websocket: WebSocketServerProtocol, *args, **kwargs):
    print(f"New Connection detected: {websocket.id}")
    CONNECTIONS.add(websocket)

    await websocket.send("You have connected.")

    await websocket.send(f'Available rooms: {list(ROOMS.keys())}. Choose on of the rooms for further chatting.')

    try:
        while True:
            event = await websocket.recv()
            event = json.loads(event)
            await mapping[event['event']](websocket, event['data'])

    except ConnectionClosedOK as disconnected:
        CONNECTIONS.remove(websocket)

        websockets.broadcast(CONNECTIONS, f"Disconnected: {websocket.id}")

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
