import asyncio
import time
from math import sqrt, ceil

"""
https://github.com/PacktPublishing/AdvancedPythonProgramming/tree/master/Chapter17


# Почему выполнение в асинхронном формате длится дольше в текущей программе, чем в синхронном:

# However, the fact that there are asynchronous versions of traditionally blocking functions
# in Python with potentially different APIs means that you will need to familiarize yourself
# with those APIs from separate functions. Another way to handle blocking functions
# without having to implement their coroutine versions is to use an executor to run the
# functions in separate threads or separate processes, to avoid blocking the thread of the
# main event loop.

#
# Asynchronous programming alone can only provide improvements in speed if all
# processing tasks are non-blocking
"""

numbers = [9637529763296797, 9637529763296797, 2147483647, 157, 36245623562456347562457]


def is_prime(number: int) -> bool:
    print(f"Processing {number} ... ")
    if number <= 2:
        print(f'{number} is NOT Prime')
        return False

    largest_divider = ceil(sqrt(number)) # blocking ?
    for divider in range(2, largest_divider + 1):
        if number % divider == 0: # blocking ?
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
            # It is typically used as asyncio.sleep(0) , to cause an immediate task switching event.
            await asyncio.sleep(0)  # ПЕРЕДАЕМ УПРАВЛЕНИЕ В ДРУГОЙ ПРОЦЕСС

    print(f'{number} Is Prime')


async def main():
    print(some_var)

    # создаем список корутин (async def - корутина)
    # create_task - добавляет корутину в тукущую очередь задач
    tasks = [loop.create_task(async_is_prime(number)) for number in numbers]

    # This function is also a coroutine, and hence, it can be used to
    # switch tasks. It takes in a sequence (usually a list) of futures and waits for them to
    # complete their execution
    await asyncio.wait(tasks)


if __name__ == '__main__':
    try:
        some_var = 7
        start = time.time()
        loop = asyncio.get_event_loop()

        # run_until_complete:
        # - берет основную корутину асинхронной программы
        # - возвращает соотвестсвующий  future
        # - блокирует ниженаписанный код до тех пор, пока не будет возвращен результат работы всех корутин
        loop.run_until_complete(main())
        asyncio.run(main())


        finish = time.time()
        print(f"{finish - start}")
    except Exception as e:
        print(f'There was a problem: {e}')




