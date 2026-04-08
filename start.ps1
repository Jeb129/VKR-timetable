# Запуск backend в отдельном окне
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend\scripts; .\dev_server.ps1"

# Запуск frontend в отдельном окне
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"