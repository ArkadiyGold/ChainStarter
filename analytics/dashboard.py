import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from web3 import Web3
import json, os

# ==================== НАСТРОЙКИ ====================
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_NAME = os.environ.get("DB_NAME", "chainstarter")
RPC = os.environ.get("RPC_URL", "http://127.0.0.1:8545")


BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABI_PATH = "/app/deployments/CrowdFunding.abi.json"
ADDR_PATH = "/app/deployments/contract-address.json"

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ==================== ПОДКЛЮЧЕНИЯ ====================
@st.cache_resource
def get_engine():
    return create_engine(DB_URL)

@st.cache_resource
def get_web3():
    w3 = Web3(Web3.HTTPProvider(RPC))
    with open(ABI_PATH) as f:
        abi = json.load(f)
    with open(ADDR_PATH) as f:
        addr = json.load(f)["address"]
    return w3, w3.eth.contract(address=addr, abi=abi)

engine = get_engine()
try:
    w3, contract = get_web3()
    accounts = w3.eth.accounts
    web3_ok = True
except Exception as e:
    web3_ok = False
    web3_err = str(e)

# ==================== UI ====================
st.set_page_config(page_title="ChainStarter", layout="wide", page_icon="🚀")
st.sidebar.title("🚀 ChainStarter")
page = st.sidebar.radio("Меню", [
    "📋 Список кампаний",
    "🔍 Детали кампании",
    "➕ Создать кампанию",
    "📊 Аналитика",
])

if web3_ok:
    st.sidebar.success(f"Web3 OK: {contract.address[:8]}…")
else:
    st.sidebar.error(f"Web3 недоступен: {web3_err}")

# ==================== SQL ====================
SQL_CAMPAIGNS = """
SELECT 
    (c.event_data->>'campaignId')::INT AS campaign_id,
    c.event_data->>'creator' AS creator,
    (c.event_data->>'goal')::NUMERIC / 1e18 AS goal_eth,
    COALESCE(SUM((f.event_data->>'amount')::NUMERIC), 0) / 1e18 AS raised_eth,
    TO_TIMESTAMP((c.event_data->>'deadline')::BIGINT) AS deadline,
    CASE 
        WHEN COALESCE(SUM((f.event_data->>'amount')::NUMERIC), 0) >= (c.event_data->>'goal')::NUMERIC 
            THEN 'success'
        WHEN TO_TIMESTAMP((c.event_data->>'deadline')::BIGINT) < NOW() 
            THEN 'failed'
        ELSE 'active'
    END AS status
FROM raw_events c
LEFT JOIN raw_events f 
    ON f.event_name = 'Contributed' 
    AND f.event_data->>'campaignId' = c.event_data->>'campaignId'
WHERE c.event_name = 'CampaignCreated'
GROUP BY c.event_data
ORDER BY campaign_id
"""

# ==================== ЭКРАН 1 ====================
if page == "📋 Список кампаний":
    st.title("Кампании")
    df = pd.read_sql(SQL_CAMPAIGNS, con=engine)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего кампаний", len(df))
    col2.metric("Активных", int((df["status"] == "active").sum()))
    col3.metric("Успешных", int((df["status"] == "success").sum()))
    col4.metric("Собрано (ETH)", f"{df['raised_eth'].sum():.2f}")

    st.dataframe(df, use_container_width=True)

# ==================== ЭКРАН 2 ====================
elif page == "🔍 Детали кампании":
    st.title("Детали кампании")
    df = pd.read_sql(SQL_CAMPAIGNS, con=engine)
    if df.empty:
        st.warning("Нет кампаний")
        st.stop()

    campaign_id = st.selectbox("Выберите ID", df["campaign_id"].tolist())
    row = df[df["campaign_id"] == campaign_id].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Цель (ETH)", f"{row['goal_eth']:.3f}")
    col2.metric("Собрано (ETH)", f"{row['raised_eth']:.3f}")
    col3.metric("Статус", row["status"])

    progress = min(row["raised_eth"] / row["goal_eth"], 1.0) if row["goal_eth"] > 0 else 0
    st.progress(progress)
    st.caption(f"Дедлайн: {row['deadline']}  |  Автор: {row['creator']}")

    st.subheader("Вклады")
    df_contrib = pd.read_sql(f"""
        SELECT 
            event_data->>'contributor' AS sponsor,
            (event_data->>'amount')::NUMERIC / 1e18 AS amount_eth,
            block_timestamp
        FROM raw_events
        WHERE event_name = 'Contributed'
          AND (event_data->>'campaignId')::INT = {campaign_id}
        ORDER BY block_timestamp
    """, con=engine)
    st.dataframe(df_contrib, use_container_width=True)

    if web3_ok:
        st.subheader("Действия")
        account = st.selectbox("От имени", accounts, key="acct")
        amount = st.number_input("Сумма вклада (ETH)", min_value=0.01, value=0.5)
        if st.button("Внести вклад"):
            try:
                tx = contract.functions.fund(campaign_id).transact({
                    "from": account,
                    "value": w3.to_wei(amount, "ether")
                })
                w3.eth.wait_for_transaction_receipt(tx)
                st.success("Вклад внесён. Обновите страницу через 5–10 сек.")
            except Exception as e:
                st.error(f"Ошибка: {e}")

# ==================== ЭКРАН 3 ====================
elif page == "➕ Создать кампанию":
    st.title("Создать кампанию")
    if not web3_ok:
        st.error("Web3 недоступен — проверьте ноду Hardhat")
        st.stop()

    with st.form("create"):
        goal = st.number_input("Цель (ETH)", min_value=0.1, value=1.0)
        days = st.number_input("Срок (дней)", min_value=1, value=7)
        author = st.selectbox("Автор", accounts)
        submitted = st.form_submit_button("Создать")

    if submitted:
        try:
            duration = int(days) * 86400
            tx = contract.functions.createCampaign(
                w3.to_wei(goal, "ether"), duration
            ).transact({"from": author})
            w3.eth.wait_for_transaction_receipt(tx)
            st.success("Кампания создана. Появится в списке через 5–10 сек.")
        except Exception as e:
            st.error(f"Ошибка: {e}")

# ==================== ЭКРАН 4 ====================
elif page == "📊 Аналитика":
    st.title("Аналитика")
    df = pd.read_sql(SQL_CAMPAIGNS, con=engine)

    col1, col2, col3 = st.columns(3)
    col1.metric("Всего кампаний", len(df))
    col2.metric("Всего собрано (ETH)", f"{df['raised_eth'].sum():.2f}")
    col3.metric("Средний сбор (ETH)", f"{df['raised_eth'].mean():.3f}")

    st.subheader("Статусы кампаний")
    st.bar_chart(df["status"].value_counts())

    st.subheader("Топ-5 спонсоров")
    df_top = pd.read_sql("""
        SELECT 
            event_data->>'contributor' AS sponsor,
            SUM((event_data->>'amount')::NUMERIC) / 1e18 AS total_eth
        FROM raw_events
        WHERE event_name = 'Contributed'
        GROUP BY sponsor
        ORDER BY total_eth DESC
        LIMIT 5
    """, con=engine)
    st.bar_chart(df_top.set_index("sponsor")["total_eth"])

    st.subheader("Топ-10 кампаний по сбору")
    st.dataframe(
        df.sort_values("raised_eth", ascending=False).head(10),
        use_container_width=True
    )