import re

from eth_account import Account
from eth_account.account import LocalAccount

Account.enable_unaudited_hdwallet_features()


def get_private_keys(value: str) -> list:
    valid_private_keys: list[str] = []

    seed_phrase_pattern = r'(\b\w+\b(?:\s+\b\w+\b){11,23})'
    private_key_pattern = r'\b(0x[0-9a-fA-F]{64}|[0-9a-fA-F]{64})\b'

    seed_phrases = re.findall(seed_phrase_pattern, value)
    private_keys = re.findall(private_key_pattern, value)

    if private_keys:
        for current_private_key in private_keys:
            try:
                account: LocalAccount = Account.from_key(private_key=current_private_key
                if current_private_key.startswith('0x') else f'0x{current_private_key}')

                valid_private_keys.append(account.key.hex())

            except Exception:
                continue

    if seed_phrases:
        for current_seed_phrase in seed_phrases:
            try:
                account: LocalAccount = Account.from_mnemonic(current_seed_phrase)

                valid_private_keys.append(account.key.hex())

            except Exception:
                continue

    return list(set(valid_private_keys))
