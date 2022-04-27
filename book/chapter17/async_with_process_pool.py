import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from math import sqrt, ceil

"""
While the output that you receive might be different in the specific times it took to run
either program, it should be the case that, as we discussed, the asynchronous program
actually took longer to run than the synchronous (sequential) one. Again, this is because the
number crunching tasks inside our is_prime() coroutine are blocking, and, instead of
overlapping these tasks in order to gain additional speed, our asynchronous program
simply switched between these tasks in its execution. In this case, only responsiveness is
achieved through asynchronous programming.

However, this does not mean that if your program contains blocking functions,
asynchronous programming is out of the question. As mentioned previously, all execution
in an asynchronous program, if not specified otherwise, occurs entirely in the same thread
and process, and blocking CPU-bound tasks can thus prevent program instructions from
overlapping each other. However, this is not the case if the tasks are distributed to separate
threads/processes. In other words, threading and multiprocessing can help asynchronous
programs with blocking instructions to achieve better execution time.


"""

numbers = [9637529763296797, 9637529763296797, 2147483647, 157, 36245623562456347562457]


def is_prime(number: int) -> bool:
    print(f"Processing {number} ... ")
    if number <= 2:
        print(f'{number} is NOT Prime')
        return False

    largest_divider = ceil(sqrt(number))
    for divider in range(2, largest_divider + 1):
        if number % divider == 0:
            print(f'{number} is NOT Prime')
            return False

    print(f'{number} is Prime')
    return True


async def async_is_prime(number: int) -> bool:
    print(f"Processing {number}... ")
    if number <= 2:
        print(f"{number} Not Prime")

    largest_divider = ceil(sqrt(number))
    for divider in range(2, largest_divider + 1):
        if number % divider == 0:
            print(f"{number} Not Prime")
            return
        if divider % 10000 == 0:
            await asyncio.sleep(0)  # ПЕРЕДАЕМ УПРАВЛЕНИЕ В ДРУГОЙ ПРОЦЕСС

    print(f'{number} Is Prime')


async def main():
    tasks = [
        loop.run_in_executor(executor, is_prime, number)
        for number in numbers
    ]

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    try:
        start = time.time()
        executor = ProcessPoolExecutor(max_workers=5)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
        finish = time.time()
        print(f"{finish - start}")
    except Exception as e:
        print('There was a problem:')
        print(str(e))
    finally:
        loop.close()


