import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from math import sqrt, ceil

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
