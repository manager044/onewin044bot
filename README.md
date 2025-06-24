# Telegram Landing Bot

Бот для управления лендингами: добавление, генерация ссылок и удаление.  
Развёртывается на Render с использованием Python 3.10.

## Команды
- `/start` — главное меню
- `/addland` — добавить ленд
- `/getlink` — получить ссылку по домену
- `/deleteland` — удалить ленд

## Установка

1. Добавь переменную окружения:
   ```
   BOT_TOKEN=твой_токен
   ```

2. Убедись, что файл `runtime.txt` содержит:

   ```
   python-3.10.13
   ```

3. Render настройки:
   - Build: `pip install -r requirements.txt`
   - Start: `python bot.py`
