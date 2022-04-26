import time

from book.chapter17.async_basic import is_prime


def test_is_prime():
    start = time.time()
    numbers = [9637529763296797, 9637529763296797, 2147483647, 157, 36245623562456347562457]
    answers = {9637529763296797: True,
               9637529763296797: True,
               2147483647: True,
               157: True,
               36245623562456347562457: False}

    results = {number: is_prime(number) for number in numbers}
    finish = time.time()
    print(finish - start)

    assert answers == results
