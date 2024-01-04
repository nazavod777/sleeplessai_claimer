import asyncio
from itertools import cycle
from math import fsum
from os import mkdir
from os.path import exists
from sys import stderr

from better_proxy import Proxy
from loguru import logger

from core import claimer
from utils import get_private_keys, flatten_list

logger.remove()
logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                          ' | <level>{level: <8}</level>'
                          ' | <cyan>{line}</cyan>'
                          ' - <white>{message}</white>')


async def main() -> list[float]:
    tasks: list = [
        asyncio.create_task(coro=claimer(semaphore=semaphore,
                                         private_key=private_key,
                                         proxy=next(proxies_cycled) if proxies_cycled else None))
        for private_key in private_keys
    ]

    return list(await asyncio.gather(*tasks))


if __name__ == '__main__':
    if not exists(path='result'):
        mkdir(path='result')

    with open(file='data/private_keys.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        private_keys: list[str] = flatten_list(nested_list=[get_private_keys(value=row.strip()) for row in file])

    with open(file='data/proxies.txt',
              mode='r',
              encoding='utf-8-sig') as file:
        proxies_list: list[str] = [Proxy.from_str(proxy=row.strip()).as_url for row in file]

    logger.info(f'Загружено {len(private_keys)} Private-Keys | {len(proxies_list)} Proxies')

    threads: int = int(input('\nThreads: '))
    print()

    if proxies_list:
        proxies_cycled: cycle = cycle(proxies_list)

    else:
        proxies_cycled: None = None

    semaphore: asyncio.Semaphore = asyncio.Semaphore(value=threads)

    claimed_amount: float = fsum(asyncio.run(main()))

    logger.success('Работа успешно завершена')
    input('\nPress Enter to Exit..')
