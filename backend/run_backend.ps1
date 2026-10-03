# 1. Запуск службы PostgreSQL
Write-Host ">>> Starting PostgreSQL service..." -ForegroundColor Cyan
Start-Service postgresql* -ErrorAction SilentlyContinue

# 2. Нахождение утилиты psql.exe
$PSQL_PATH = "psql"
if (-not (Get-Command "psql" -ErrorAction SilentlyContinue)) {
    # Автопоиск psql в стандартной папке установки PostgreSQL на Windows
    $foundPsql = Get-ChildItem "C:\Program Files\PostgreSQL" -Recurse -Filter "psql.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($foundPsql) {
        $PSQL_PATH = $foundPsql.FullName
    } else {
        Write-Host "[!] psql.exe not found in PATH or Program Files. Please check PostgreSQL installation." -ForegroundColor Red
    }
}

# 3. Настройки подключения
$DB_USER = "postgres"
$DB_NAME = "chainstarter"
$DB_PORT = "5432"

# 4. Применение SQL-файлов
Write-Host ">>> Applying SQL files to $DB_NAME..." -ForegroundColor Cyan

if (Test-Path "schema.sql") {
    Get-Content "schema.sql" | & $PSQL_PATH -U $DB_USER -d $DB_NAME -p $DB_PORT
}

if (Test-Path "marts.sql") {
    Get-Content "marts.sql" | & $PSQL_PATH -U $DB_USER -d $DB_NAME -p $DB_PORT
    Write-Host ">>> Views from marts.sql applied successfully!" -ForegroundColor Green
} else {
    Write-Host ">>> File marts.sql not found!" -ForegroundColor Yellow
}

# 5. Запуск Python-скрипта
Write-Host ">>> Starting ingest.py..." -ForegroundColor Cyan
python ingest.py