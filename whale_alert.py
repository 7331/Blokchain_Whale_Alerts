#!/usr/bin/env python3.9

import requests
import time
from typing import Optional
import random

_REQUESTS_TIMEOUT = 10
_SEEN_TX_HASHES: set[str] = set()
_MIN_VALUE = 25_000_000
_SECONDS_BETWEEN_NOTIFS = 60
_UNKNOWN_WALLET_NAME = 'an unknown wallet'
_WEBHOOK_URL = ''


def _get_owner_name(tx: dict) -> str:
    owner_name: str = tx['owner_type']
    if owner_name == 'unknown':
        owner_name = _UNKNOWN_WALLET_NAME
    elif owner_name == 'exchange':
        owner_name = tx['owner'].upper()

    return owner_name


with requests.Session() as s:
    while True:
        try:
            start = int(time.time()) - 60
            r = s.get(f'https://api.whale-alert.io/v1/transactions?api_key=V1G0FY73xPWLmHHXgmnhJuaHninO3wZk&start={start}&min_value={_MIN_VALUE}', timeout=_REQUESTS_TIMEOUT)
            transactions: Optional[list[dict]] = r.json().get('transactions')

            if transactions:
                for tx in transactions:
                    tx_hash: str = tx['hash']

                    if tx_hash not in _SEEN_TX_HASHES:
                        from_owner = _get_owner_name(tx['from'])
                        to_owner = _get_owner_name(tx['to'])

                        tx_amount: int = tx['amount']
                        description = f':rotating_light: {tx_amount:,} {tx["symbol"].upper()} '

                        tx_amount_usd: int = tx['amount_usd']
                        if tx_amount != tx_amount_usd:
                            description += f'(${tx_amount_usd:,}) '

                        description += tx['transaction_type'].replace('transfer', 'transferred').replace('mint', 'minted') + ' '

                        if from_owner == to_owner and from_owner != _UNKNOWN_WALLET_NAME:
                            description += f'within **{from_owner}** '
                        else:
                            description += f'from **{from_owner}** to **{to_owner}** '

                        description += ':rotating_light:'

                        embed = {'embeds': [{'description': description, 'color': random.randint(0, 0xFFFFFF)}], 'username': 'Whale Alert', 'avatar_url': 'https://pbs.twimg.com/profile_images/1132579647374417921/9ifIGXEQ_400x400.png'}
                        r = s.post(_WEBHOOK_URL, json=embed, timeout=_REQUESTS_TIMEOUT)
                        r.raise_for_status()
                        _SEEN_TX_HASHES.add(tx_hash)
                        break

        except Exception as e:
            print(f'{repr(e)} - {tx}\n')

        print(f'Sleeping for {_SECONDS_BETWEEN_NOTIFS} seconds...')
        time.sleep(_SECONDS_BETWEEN_NOTIFS)