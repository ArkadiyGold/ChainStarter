import json, random, os
from web3 import Web3

RPC = os.environ.get("RPC_URL", "http://127.0.0.1:8545")
w3 = Web3(Web3.HTTPProvider(RPC))

# Путь к файлам деплоя
BASE = "/app/deployments"
with open(os.path.join(BASE, "CrowdFunding.abi.json")) as f:
    abi = json.load(f)
with open(os.path.join(BASE, "contract-address.json")) as f:
    addr = json.load(f)["address"]

contract = w3.eth.contract(address=addr, abi=abi)
accounts = w3.eth.accounts

print(f"Аккаунтов: {len(accounts)}")
print(f"Контракт: {addr}")

# =============== 100 кампаний ===============
print("\n[1/2] Создаю 100 кампаний...")
created = 0
for i in range(100):
    author = random.choice(accounts)
    goal = w3.to_wei(random.uniform(1, 10), "ether")
    duration = random.randint(86400, 604800)  # 1-7 дней в секундах
    try:
        tx = contract.functions.createCampaign(goal, duration).transact({"from": author})
        w3.eth.wait_for_transaction_receipt(tx)
        created += 1
    except Exception as e:
        print(f"  ошибка на кампании {i}: {e}")
    if i % 20 == 0:
        print(f"  {i}/100")
print(f"Создано кампаний: {created}")

# =============== 500 вкладов ===============
print("\n[2/2] Делаю 500 вкладов...")
ok, fail = 0, 0
for i in range(500):
    contributor = random.choice(accounts)
    campaign_id = random.randint(1, 100)
    value = w3.to_wei(random.uniform(0.1, 2), "ether")
    try:
        tx = contract.functions.fund(campaign_id).transact({
            "from": contributor, "value": value
        })
        w3.eth.wait_for_transaction_receipt(tx)
        ok += 1
    except Exception as e:
        fail += 1
        if fail <= 5:
            print(f"  ошибка на вкладе {i}: {e}")
    if i % 50 == 0:
        print(f"  {i}/500")

print(f"\nГотово. Успешных вкладов: {ok}, отклонённых: {fail}")