import aiohttp
import pyuseragents
import asyncio
import random
import json
from eth_account import Account
from eth_account.signers.local import LocalAccount
from loguru import logger
from web3 import Web3, types


w3 = Web3(Web3.HTTPProvider('https://1rpc.io/zksync2-era'))
abi = json.load(open('./abi.json'))
claim_contract = w3.eth.contract(w3.to_checksum_address('0x95702a335e3349d197036Acb04BECA1b4997A91a'), abi=abi)
headers = {
        'authority': 'www.zksyncpepe.com',
        'scheme': 'https',
        'cache-control': 'no-cache',
        'accept': 'application/json, text/plain, */*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uk-UA;q=0.6,uk;q=0.5',
        'referer': 'https://www.zksyncpepe.com/airdrop',
        'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': pyuseragents.random(),}


async def check(account, session, result_list):
    address = account.address.lower()
    retries = 3
    delay = 5
    while retries > 0:
        try:
            # First URL
            amount_url = f'https://www.zksyncpepe.com/resources/amounts/{address}.json'
            async with session.get(amount_url) as amount_response:
                if amount_response.status == 200:
                    amount = await amount_response.json()


            # Second URL
            proofs_url = f'https://www.zksyncpepe.com/resources/proofs/{address}.json'
            async with session.get(proofs_url) as proofs_response:
                if proofs_response.status == 200:
                    proof = await proofs_response.json()
            result_list.append([amount, proof])
            break
        except aiohttp.ClientError as e:
            print(f"Request failed for {address}. Retrying in {delay} seconds.")
            retries -= 1
            await asyncio.sleep(delay)
            delay *= random.uniform(1, 2)  # random delay here
            continue



async def claim(account: LocalAccount, proof: list[str], amount: int) -> None:
    tx_params: types.TxParams = {
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
        'maxFeePerGas': 0,
        'maxPriorityFeePerGas': 0,
        'gas': 0
    }
    
    tx = claim_contract.functions.claim(
        proof, w3.to_wei(amount, "ether")
    ).build_transaction(tx_params)
    tx.update({'maxFeePerGas': w3.eth.gas_price})
    tx.update({'maxPriorityFeePerGas': w3.eth.gas_price})


    try:
        gasLimit = Web3.to_wei(float(Web3.from_wei(w3.eth.estimate_gas(tx), 'ether')) / 1.2, 'ether')
        tx.update({'gas': gasLimit})
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        logger.success(
            f"Claimed successfully {amount} tokens from {account.address}. Tx: https://explorer.zksync.io/tx/{tx_hash.hex()}"
        )
    except Exception as ex:
        logger.error(f"{account.address}. Error: {ex}")


async def main():
    logger.add('./logs/{time}.log')
    print('''
  ______                                   __                 ______                           __                 
 /      \                                 /  |               /      \                         /  |                
/$$$$$$  |  ______   __    __   ______   _$$ |_     ______  /$$$$$$  | _____  ____    ______  $$ |____    ______  
$$ |  $$/  /      \ /  |  /  | /      \ / $$   |   /      \ $$ |__$$ |/     \/    \  /      \ $$      \  /      \ 
$$ |      /$$$$$$  |$$ |  $$ |/$$$$$$  |$$$$$$/   /$$$$$$  |$$    $$ |$$$$$$ $$$$  |/$$$$$$  |$$$$$$$  | $$$$$$  |
$$ |   __ $$ |  $$/ $$ |  $$ |$$ |  $$ |  $$ | __ $$ |  $$ |$$$$$$$$ |$$ | $$ | $$ |$$    $$ |$$ |  $$ | /    $$ |
$$ \__/  |$$ |      $$ \__$$ |$$ |__$$ |  $$ |/  |$$ \__$$ |$$ |  $$ |$$ | $$ | $$ |$$$$$$$$/ $$ |__$$ |/$$$$$$$ |
$$    $$/ $$ |      $$    $$ |$$    $$/   $$  $$/ $$    $$/ $$ |  $$ |$$ | $$ | $$ |$$       |$$    $$/ $$    $$ |
 $$$$$$/  $$/        $$$$$$$ |$$$$$$$/     $$$$/   $$$$$$/  $$/   $$/ $$/  $$/  $$/  $$$$$$$/ $$$$$$$/   $$$$$$$/ 
                    /  \__$$ |$$ |                                                                                
                    $$    $$/ $$ |                                                                                
                     $$$$$$/  $$/                                                                                 

          ''')
    accounts = []
    with open("wallets.txt", "r", encoding="utf8") as file:
        accounts: list[LocalAccount] = [
            Account.from_key(line.strip())
            for line in file.read().split("\n")
            if line != ""
        ]
    result_list = []
    async with aiohttp.ClientSession(headers=headers) as session:
        result_list = []
        for account in accounts:
            await check(account, session, result_list)
            # Introduce an asynchronous delay between requests (adjust this delay as needed)
    # Extracting amounts and proofs from the result_list
    amounts = [result[0] for result in result_list]
    proofs = [result[1] for result in result_list]
    # Claim tokens for each account with its respective amount and proof
    claim_tasks = [
        claim(account, proof, amount[0])
        for account, proof, amount in zip(accounts, proofs, amounts)
    ]
    await asyncio.gather(*claim_tasks)


print(asyncio.run(main()))




