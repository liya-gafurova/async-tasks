import asyncio
import time


async def count_down(literal, delay):
    n = 3

    tab = " " * (ord(literal) + n)

    while n:
        await asyncio.sleep(delay)

        print(f"{tab} {literal} = {n}")

        n -= 1


async def main():
    args = [("A", 2), ("B", 1), ("C", 0.8)]
    tasks = [loop.create_task(count_down(*arg)) for arg in args]

    await asyncio.wait(tasks)


if __name__ == "__main__":
    start = time.time()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    finish = time.time()

    print(f"Took: {finish - start}") # Took: 6.005645036697388




