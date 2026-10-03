# ChainStarter — Backend & Data Pipeline

Бэкенд-часть сервиса краудфандинга ChainStarter. Отвечает за прослушивание событий смарт-контракта в локальной сети блокчейн (Hardhat/Ethereum), их сохранение в PostgreSQL и автоматическое формирование SQL-витрин для аналитического дашборда.

---

## 🛠 Технологический стек
* **Python 3.10+** (web3.py, psycopg2-binary)
* **PostgreSQL 16** (база данных & SQL Views)
* **Hardhat** (локальная сеть блокчейн)
* **PowerShell** (скрипты автоматизации развертывания)

---

## 🚀 Быстрый запуск бэкенда (One-Click Launch)

Для удобства команды в проекте настроен автоматический скрипт `run_backend.ps1`, который самостоятельно запускает службу PostgreSQL, применяет схемы базы данных и накатывает SQL-витрины перед запуском слушателя.

### 1. Предварительные требования
Убедитесь, что в отдельном терминале запущен локальный узел Hardhat:
```powershell
npx hardhat node
```

### 2. Пошаговая установка и запуск

1. **Перейдите в корневую папку проекта:**
   ```powershell
   cd chainstarter-contracts
   ```

2. **Разрешите выполнение скриптов в текущей сессии PowerShell:**
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   ```

3. **Создайте виртуальное окружение Python (если его еще нет):**
   ```powershell
   python -m venv .venv
   ```

4. **Активируйте виртуальное окружение:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

5. **Установите необходимые зависимости:**
   ```powershell
   pip install -r .\backend\requirements.txt
   ```

6. **Запустите автоматический пайплайн:**
   ```powershell
   .\backend\run_backend.ps1
   ```

---

## ⚠️ Возможные проблемы и их решение

### Ошибка `TerminatorExpectedAtEndOfString` при запуске скрипта
Если PowerShell выдает синтаксическую ошибку в строке со скриптом `Write-Host`, это связано с неверной кодировкой файла `run_backend.ps1` (конфликт UTF-8 и Windows-1251).

**Решение:**
1. Откройте файл `backend/run_backend.ps1` в VS Code.
2. В нижнем правом углу нажмите на текущую кодировку (например, `UTF-8`).
3. Выберите **«Save with Encoding»** (Сохранить с кодировкой).
4. Выберите **UTF-8 с сигнатурой (UTF-8 with BOM)** и сохраните файл.

**Альтернативное решение (ручной запуск бэкенда в обход скрипта):**
```powershell
# 1. Активируйте окружение из корня
.\.venv\Scripts\Activate.ps1

# 2. Перейдите в папку бэкенда
cd backend

# 3. Запустите парсер напрямую
python ingest.py
```
