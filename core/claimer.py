import asyncio
from json import load
from random import choice

import aiohttp
from aiohttp_proxy import ProxyConnector
from eth_account import Account
from eth_account.account import LocalAccount
from loguru import logger
from pyuseragents import random as random_useragent
from web3 import Web3
from web3.auto import w3
from web3.eth import AsyncEth
from web3.exceptions import ContractLogicError
from web3.exceptions import TimeExhausted

from data import config, constants
from utils import append_file
from utils import get_gwei, get_nonce, get_chain_id

with open(file='data/contract_abi.json',
          mode='r',
          encoding='utf-8-sig') as file:
    contract_abi: dict = load(file)


class InsufficientBalance(BaseException):
    pass


class Claimer:
    def __init__(self,
                 private_key: str) -> None:
        self.private_key: str = private_key
        self.account: LocalAccount = Account.from_key(private_key=private_key)

    async def get_tx_data(self,
                          client: aiohttp.ClientSession) -> tuple[int | None, list | None]:
        r: None = None

        while True:
            try:
                r: aiohttp.ClientResponse = await client.get(url='https://www.sleeplessai.net/airdrop/info',
                                                             params={
                                                                 'account': self.account.address
                                                             })

                if not await r.json(content_type=None):
                    return None, None

                return (int((await r.json(content_type=None))['amount']),
                        (await r.json(content_type=None))['proof'])

            except Exception as error:
                if r:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при получении данных для транзакции: '
                                 f'{error}, ответ: {await r.text()}')

                else:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при получении данных для транзакции: '
                                 f'{error}')

    async def send_tx(self,
                      proof: list,
                      amount: int,
                      provider) -> bool:
        chain_id: int = await get_chain_id(provider=provider)
        contract = provider.eth.contract(address=constants.CLAIM_CONTRACT_ADDRESS,
                                         abi=contract_abi)

        while True:
            try:
                nonce: int = await get_nonce(provider=provider,
                                             address=self.account.address)

                if config.GWEI and str(config.GWEI).isdigit() and config.GWEI > 0:
                    gwei: int = w3.to_wei(number=config.GWEI,
                                          unit='gwei')

                else:
                    gwei: int = await get_gwei(provider=provider)

                transaction_data: dict = await contract.functions.claim(proof,
                                                                        amount).build_transaction({
                    'gasPrice': gwei,
                    'from': self.account.address,
                    'nonce': nonce,
                    'chainId': chain_id
                })

                gas: int = await provider.eth.estimate_gas(transaction=transaction_data)

            except ContractLogicError as error:
                logger.error(f'{self.private_key} | Ошибка при симуляции транзакции: {error}')

                if 'insufficient balance' in str(error) or 'execution reverted' in str(error):
                    raise InsufficientBalance(self.private_key)

            except Exception as error:
                logger.error(f'{self.private_key} | Неизвестная ошибка при симуляции транзакции: {error}')

                if 'gas required exceeds allowance' in str(error) or 'execution reverted' in str(error):
                    raise InsufficientBalance(self.private_key)

                await asyncio.sleep(delay=3)

            else:
                break

        transaction_data: dict = await contract.functions.claim(proof,
                                                                amount).build_transaction({
            'gasPrice': gwei,
            'from': self.account.address,
            'nonce': nonce,
            'chainId': chain_id,
            'gas': gas
        })

        signed_transaction = provider.eth.account.sign_transaction(transaction_dict=transaction_data,
                                                                   private_key=self.account.key)

        while True:
            try:
                await provider.eth.send_raw_transaction(signed_transaction.rawTransaction)

            except Exception as error:
                if 'already known' in str(error):
                    break

                if 'nonce too low' in str(error) or 'nonce too high' in str(error):
                    return await self.send_tx(provider=provider,
                                              proof=proof,
                                              amount=amount)

                logger.error(f'{self.private_key} | Неизвестная ошибка при отправке TX: {error}')

                await asyncio.sleep(delay=3)

            else:
                break

        transaction_hash: str = w3.to_hex(w3.keccak(signed_transaction.rawTransaction))
        logger.info(f'{self.private_key} | {transaction_hash} - {amount / 10 ** 18}')

        if config.WAIT_TX_RESULT:
            while True:
                try:
                    transaction_response = await provider.eth.wait_for_transaction_receipt(
                        transaction_hash=transaction_hash,
                        poll_latency=3,
                        timeout=3600)

                except TimeExhausted:
                    logger.error(f'{self.private_key} | Не удалось дождаться завершения транзакции, TX Hash: '
                                 f'{transaction_hash}, жду еще раз')

                except Exception as error:
                    logger.error(f'{self.private_key} | Неизвестная ошибка при ожидании результата TX Hash: '
                                 f'{transaction_hash}: {error}')

                else:
                    break

            if transaction_response['status'] == 1:
                logger.success(f'{self.private_key} | {transaction_hash} - {amount / 10 ** 18}')
                return True

            logger.error(f'{self.private_key} | TX Failed - {transaction_hash}')
            return False

        return True

    async def start_claimer(self,
                            proxy: str | None = None) -> float:
        async with aiohttp.ClientSession(connector=ProxyConnector.from_url(url=proxy) if proxy else None,
                                         headers={
                                             'accept': 'application/json, text/plain, */*',
                                             'accept-language': 'ru,en;q=0.9,vi;q=0.8,es;q=0.7,cy;q=0.6',
                                             'referer': 'https://www.sleeplessai.net/airdrop',
                                             'user-agent': random_useragent()
                                         }) as client:
            tx_data: tuple[int | None, list | None] = await self.get_tx_data(client=client)

            if not tx_data[0] or not tx_data[1]:
                logger.info(f'{self.private_key} | Not Eligible')
                return 0

        provider = Web3(Web3.AsyncHTTPProvider(endpoint_uri=choice(config.RPC_URLS_LIST),
                                               request_kwargs={
                                                   'proxy': proxy
                                                   if proxy and config.USE_PROXY_FOR_RPC else None
                                               }),
                        modules={'eth': (AsyncEth,)},
                        middlewares=[])

        tx_result: bool = await self.send_tx(proof=tx_data[1],
                                             amount=tx_data[0],
                                             provider=provider)

        if not tx_result:
            await append_file(folder='result/failed_transaction.txt',
                              content=self.private_key)
            return 0

        return tx_data[0] / 10 ** 18


async def claimer(semaphore: asyncio.Semaphore,
                  private_key: str,
                  proxy: str | None = None) -> float:
    async with semaphore:
        try:
            return_amount: float = await Claimer(private_key=private_key).start_claimer(proxy=proxy)

        except InsufficientBalance:
            logger.error(f'{private_key} | Insufficient Balance')

            await append_file(folder='result/insufficient_balance.txt',
                              content=private_key)

            return 0

        except ValueError as error:
            logger.error(f'{private_key} | Unexpected Error: {error}')

            await append_file(folder='result/unexpected_error.txt',
                              content=private_key)

            return 0

        else:
            if return_amount > 0:
                await append_file(folder='result/claimed.txt',
                                  content=f'{private_key}:{return_amount}')

            return return_amount
