import os
import time
import json
from datetime import datetime, timezone
from web3 import Web3
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", 5432))
DB_NAME = os.environ.get("DB_NAME", "chainstarter")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

RPC = os.environ.get("RPC_URL", "http://127.0.0.1:8545")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=str(DB_PASSWORD),
        client_encoding='utf8'
    )

def load_deployments():
    abi_path = "/app/deployments/CrowdFunding.abi.json"
    addr_path = "/app/deployments/contract-address.json"

    with open(abi_path, "r", encoding="utf-8") as f:
        abi = json.load(f)

    with open(addr_path, "r", encoding="utf-8") as f:
        deploy_info = json.load(f)

    return abi, deploy_info["address"], deploy_info.get("deployBlock", 0)
def init_db(conn):
    base_dir = os.path.dirname(__file__)
    schema_path = os.path.join(base_dir, "schema.sql")
    marts_path = os.path.join(base_dir, "marts.sql")

    with conn.cursor() as cursor:
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                cursor.execute(f.read())
        if os.path.exists(marts_path):
            with open(marts_path, "r", encoding="utf-8") as f:
                cursor.execute(f.read())
    conn.commit()
    print("[+] Структура БД и витрины успешно инициализированы!")
def main():
    w3 = Web3(Web3.HTTPProvider(RPC))
    if not w3.is_connected():
        print(f"[-] Не удалось подключиться к RPC {RPC}")
        return

    abi, contract_address, start_block = load_deployments()
    contract = w3.eth.contract(address=contract_address, abi=abi)

    print(f"[+] Слушатель запущен. Адрес контракта: {contract_address}, Стартовый блок: {start_block}")

    conn = get_db_connection()
    cursor = conn.cursor()

    current_block = start_block

    while True:
        try:
            latest_block = w3.eth.block_number
            if current_block <= latest_block:
                # CampaignCreated
                created_events = contract.events.CampaignCreated.get_logs(from_block=current_block, to_block=latest_block)
                for event in created_events:
                    args = event['args']
                    block = w3.eth.get_block(event['blockNumber'])
                    ts = datetime.fromtimestamp(block['timestamp'], tz=timezone.utc)

                    cursor.execute(
                        """
                        INSERT INTO raw_events (transaction_hash, block_number, block_timestamp, event_name, campaign_id, event_data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            event['transactionHash'].hex(),
                            event['blockNumber'],
                            ts,
                            'CampaignCreated',
                            args['campaignId'],
                            json.dumps({
                                'campaignId': args['campaignId'],
                                'creator': args['creator'],
                                'goal': str(args['goal']),
                                'deadline': args['deadline']
                            })
                        )
                    )

                    deadline_dt = datetime.fromtimestamp(args['deadline'], tz=timezone.utc)
                    cursor.execute(
                        """
                        INSERT INTO campaigns (campaign_id, creator, goal, deadline, total_raised, claimed)
                        VALUES (%s, %s, %s, %s, 0, FALSE)
                        ON CONFLICT (campaign_id) DO NOTHING
                        """,
                        (args['campaignId'], args['creator'], args['goal'], deadline_dt)
                    )

                # Contributed
                contrib_events = contract.events.Contributed.get_logs(from_block=current_block, to_block=latest_block)
                for event in contrib_events:
                    args = event['args']
                    block = w3.eth.get_block(event['blockNumber'])
                    ts = datetime.fromtimestamp(block['timestamp'], tz=timezone.utc)

                    cursor.execute(
                        """
                        INSERT INTO raw_events (transaction_hash, block_number, block_timestamp, event_name, campaign_id, event_data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            event['transactionHash'].hex(),
                            event['blockNumber'],
                            ts,
                            'Contributed',
                            args['campaignId'],
                            json.dumps({
                                'campaignId': args['campaignId'],
                                'contributor': args['contributor'],
                                'amount': str(args['amount'])
                            })
                        )
                    )

                    cursor.execute(
                        """
                        UPDATE campaigns 
                        SET total_raised = total_raised + %s 
                        WHERE campaign_id = %s
                        """,
                        (args['amount'], args['campaignId'])
                    )

                # Refunded
                refund_events = contract.events.Refunded.get_logs(from_block=current_block, to_block=latest_block)
                for event in refund_events:
                    args = event['args']
                    block = w3.eth.get_block(event['blockNumber'])
                    ts = datetime.fromtimestamp(block['timestamp'], tz=timezone.utc)

                    cursor.execute(
                        """
                        INSERT INTO raw_events (transaction_hash, block_number, block_timestamp, event_name, campaign_id, event_data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            event['transactionHash'].hex(),
                            event['blockNumber'],
                            ts,
                            'Refunded',
                            args['campaignId'],
                            json.dumps({
                                'campaignId': args['campaignId'],
                                'contributor': args['contributor'],
                                'amount': str(args['amount'])
                            })
                        )
                    )

                    cursor.execute(
                        """
                        UPDATE campaigns 
                        SET total_raised = GREATEST(0, total_raised - %s) 
                        WHERE campaign_id = %s
                        """,
                        (args['amount'], args['campaignId'])
                    )

                # FundsClaimed
                claimed_events = contract.events.FundsClaimed.get_logs(from_block=current_block, to_block=latest_block)
                for event in claimed_events:
                    args = event['args']
                    block = w3.eth.get_block(event['blockNumber'])
                    ts = datetime.fromtimestamp(block['timestamp'], tz=timezone.utc)

                    cursor.execute(
                        """
                        INSERT INTO raw_events (transaction_hash, block_number, block_timestamp, event_name, campaign_id, event_data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            event['transactionHash'].hex(),
                            event['blockNumber'],
                            ts,
                            'FundsClaimed',
                            args['campaignId'],
                            json.dumps({
                                'campaignId': args['campaignId'],
                                'creator': args['creator'],
                                'amount': str(args['amount'])
                            })
                        )
                    )

                    cursor.execute(
                        """
                        UPDATE campaigns 
                        SET claimed = TRUE 
                        WHERE campaign_id = %s
                        """,
                        (args['campaignId'],)
                    )

                conn.commit()
                current_block = latest_block + 1

            time.sleep(2)

        except Exception as e:
            print(f"[-] Ошибка при обработке событий: {e}")
            conn.rollback()
            time.sleep(5)  

if __name__ == "__main__":
    main()