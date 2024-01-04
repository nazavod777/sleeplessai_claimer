[![Telegram channel](https://img.shields.io/endpoint?url=https://runkit.io/damiankrawczyk/telegram-badge/branches/master?url=https://t.me/n4z4v0d)](https://t.me/n4z4v0d)
[![PyPI supported Python versions](https://img.shields.io/pypi/pyversions/better-automation.svg)](https://www.python.org/downloads/release/python-3116/)
[![works badge](https://cdn.jsdelivr.net/gh/nikku/works-on-my-machine@v0.2.0/badge.svg)](https://github.com/nikku/works-on-my-machine)  

### data/config.py  
**RPC_URLS_LIST** - _Список RPC-нод BSC (можно оставить одну)_  
**USE_PROXY_FOR_RPC** - _Булевое значение, использовать-ли прокси при подключении к ноде (True / False)_  
**GWEI** - _Статик GWEI для отправки TX (если оставить 0 / установить значение None, то скрипт будет брать средний GWEI)_  
**WAIT_TX_RESULT** - _Булевая переменная, ожидать-ли завершения транзакции, или просто отправлять и идти дальше_  

### data/private_keys.txt  
_Поддерживает seed phrase / private key (скрипт в строке сам ищет приватник или мнемоник, так что можете вставлять в любом формате)_  

### data/proxies.txt
_Список прокси (можно оставить пустым)_

# DONATE (_any evm_) - 0xDEADf12DE9A24b47Da0a43E1bA70B8972F5296F2