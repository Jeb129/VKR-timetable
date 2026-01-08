if (!(Test-Path venv)) {
    Write-Output "Создание окружения..."
    python -m venv venv
}
Write-Output "Установка зависимостей..."
venv\Scripts\Activate
pip install -r requirements.txt
Write-Output "Окружение инициализировано"

