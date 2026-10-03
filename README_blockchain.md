# ChainStarter — смарт-контракт (Blockchain Developer)

Краудфандинг «всё или ничего»: если к дедлайну цель собрана — создатель забирает деньги, если нет — спонсоры возвращают свои вклады.

## Быстрый старт

```bash
npm install
npx hardhat test            # запустить тесты (8 шт.)

# терминал 1: локальная блокчейн-сеть
npx hardhat node

# терминал 2: деплой контракта
npm run deploy
```

После деплоя в папке `deployments/` появятся файлы для команды:

| Файл | Что внутри |
|---|---|
| `CrowdFunding.abi.json` | ABI контракта (для Web3.py) |
| `contract-address.json` | адрес, chainId, номер блока деплоя, аккаунт деплоя |

На свежей ноде адрес всегда `0x5FbDB2315678afecb367f032d93F642f64180aa3`.

## Функции контракта

| Функция | Кто вызывает | Условия |
|---|---|---|
| `createCampaign(goal, duration)` | любой | `goal` в wei > 0, `duration` в секундах > 0. Возвращает id (с 1) |
| `fund(id)` payable | любой | до дедлайна, сумма > 0 |
| `refund(id)` | спонсор | после дедлайна, цель НЕ достигнута, у него есть вклад |
| `claim(id)` | только создатель | после дедлайна, цель достигнута, ещё не забирал |

Читать состояние: `campaignCount()`, `campaigns(id)` → `(creator, goal, deadline, raised, claimed)`, `contributions(id, address)`.

## События (для Backend)

| Событие | Параметры |
|---|---|
| `CampaignCreated` | `campaignId` (indexed), `creator` (indexed), `goal`, `deadline` |
| `Contributed` | `campaignId` (indexed), `contributor` (indexed), `amount` |
| `Refunded` | `campaignId` (indexed), `contributor` (indexed), `amount` |
| `FundsClaimed` | `campaignId` (indexed), `creator` (indexed), `amount` |

Как определить итог кампании в аналитике:
- **успех** = кампания собрала `>= goal` (сумма `Contributed` минус ничего, т.к. при успехе возвратов нет);
- **провал** = дедлайн прошёл и сумма `Contributed` < `goal`.

Время события берётся из блока (`w3.eth.get_block(event.blockNumber).timestamp`).

## Подсказки для остальных ролей

- **Симулятор (PM):** дедлайн работает по времени блока. В локальной сети время можно «перемотать»:
  ```python
  w3.provider.make_request("evm_increaseTime", [7 * 24 * 3600])
  w3.provider.make_request("evm_mine", [])
  ```
  Кампании для симулятора удобно создавать с короткой `duration` (например, 60 секунд) и потом мотать время.
- **Docker:** чтобы нода была доступна из контейнеров, запускай её так: `npx hardhat node --hostname 0.0.0.0`.
- **Backend:** начинай читать события с `deployBlock` из `contract-address.json`.

## MetaMask (для ручной проверки)

1. Добавить сеть вручную: RPC `http://127.0.0.1:8545`, Chain ID `31337`, валюта `ETH`.
2. Импортировать любой тестовый аккаунт: приватные ключи печатает `npx hardhat node` при запуске.
3. ⚠️ Эти ключи публичные — использовать только в локальной сети.

## Структура

```
contracts/CrowdFunding.sol       основной контракт
test/CrowdFunding.test.js        тесты
scripts/deploy.js                деплой + выгрузка ABI и адреса
hardhat.config.js                конфиг (Solidity 0.8.24, сеть localhost)
```