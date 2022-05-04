import asyncio
import websockets
from websockets.legacy.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

CONNECTIONS = set()


async def async_iterator(iterable):
    for itm in iterable:
        yield itm
        await asyncio.sleep(0)


async def handler(websocket: WebSocketServerProtocol):
    print(f"New Connection detected: {websocket.id}")
    CONNECTIONS.add(websocket)

    await websocket.send("You have connected.")

    async for conn in async_iterator(CONNECTIONS):
        await conn.send(f"New Connection: {websocket.id}")

    try:
        while True:
            message = await websocket.recv()
            async for conn in async_iterator(CONNECTIONS):
                await conn.send(f"New Message: {message}")

    except ConnectionClosedOK as disconnected:
        CONNECTIONS.remove(websocket)

        async for conn in async_iterator(CONNECTIONS):
            await conn.send(f"Disconnected: {websocket.id}")

        print(f"Disconnected: {websocket.id}")

    finally:
        print("8")


async def main():
    async with websockets.serve(handler, "", 8088):  # handler is a coroutine that manages a connection. When a client connects, websockets calls handler with the connection in argument. When handler terminates, websockets closes the connection.
        await asyncio.Future()  # run forever ?


if __name__ == '__main__':
    asyncio.run(main())
