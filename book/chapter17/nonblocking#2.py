import asyncio
import time
from concurrent.futures import ProcessPoolExecutor

# Если операции внутри корутин - блокирующие - асинхроннсть работает дольше синхронности.
# Решение - добавить concurrent.futures.ProcessPoolExecutor / ThreadPoolExecutor


# Если операции внутри корутин неблокируюющие - используем просто асинхронность

# Вопрос - зачем тогда нужны multiprocessing / threading ?
def count_down(literal, delay):
    n = 3

    tab = " " * (ord(literal) + n)

    while n:
        time.sleep(delay)
        print(f"{tab} {literal} = {n}")

        n -= 1


async def main():
    args = [("A", 2), ("B", 1), ("C", 0.8)]
    tasks = [
        loop.run_in_executor(executor, count_down, *arg)
        for arg in args
    ]

    await asyncio.wait(tasks)


if __name__ == "__main__":
    start = time.time()
    executor = ProcessPoolExecutor(max_workers = 3)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    finish = time.time()

    print(f"Took: {finish - start}") # Took: 6.012678146362305




