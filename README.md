# Calendar bot backend
Бэкенд составляющая для бота календаря

## Основное

### Цель
Отображение для пользователя мероприятий текущего дня. Отправка пользователю информации об добавлении, изменении и удалении мероприятий.

### Стек технологий
- **Python**: основной язык программирования
- **Django**: основной фреймворк
- **Docker & Docker Compose**: контейнеризация проекта
- **Celery**: для выполнения задач в фоновом режиме
- **Redis**: брокер сообщений, сборщик кэша
- **PostgreSQL**: БД для хранения данных


### Как развернуть проект:
1. Клонируйте репозиторий через Git
cd <ваша директория, в которую вы хотите разместить проект>
git clone <SSH-ключ данного репозитория>
2. Устанавливаем uv
**Windows:**
```bash
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
**MacOS и Linux:**
```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
```
3. Запускаем поочередно команды:
```bash
   uv sync --all-groups
   uv run pre-commit install
   uv run pre-commit run --all-files
```
4. Скачайте и установите Docker Desktop с официального сайта: https://www.docker.com
   
5. Для локального запуска проекта необходимо выполнить следующие команды:
```bash
- docker-compose -f docker-compose.container.yml up --build
```

1. Добавление тестовых данных:
```bash
docker compose exec backend python manage.py populate_db --users 100 --collects 50 --payments 1000 --comments 2000 --likes 1500
 docker compose exec backend python manage.py update_collects
```

1. Пример заполнения .env файла:
```bash
# Django (Fake Key)
DEBUG=True
DJANGO_SECRET_KEY=secret-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,calendar-app
DJANGO_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
# PostgreSQL
POSTGRES_DB=calendar
POSTGRES_USER=calendar
POSTGRES_PASSWORD=calendar
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
DOCKER_ENV=True
# Email
EMAIL_HOST=smtp.ethereal.email #TODO заменить на реальные настройки можно использовать https://ethereal.email для тестирования
EMAIL_PORT=587 #TODO заменить на реальные настройки
EMAIL_USE_TLS=True #TODO заменить на реальные настройки
EMAIL_USE_SSL=False #TODO заменить на реальные настройки
EMAIL_HOST_USER=katrine66@ethereal.email #TODO заменить на реальные настройки
EMAIL_HOST_PASSWORD=k3KRXDRJFEbY71fERF #TODO заменить на реальные настройки
DEFAULT_FROM_EMAIL=no-reply@ylab.team #TODO заменить на реальные настройки
REDIS_HOST=redis
# Regisration
ALLOWED_EMAIL=@mail.ru
# Telegram
BOT_TOKEN=token
CHAT_ID="CHAT_ID"
CALENDAR_KEY="CALENDAR_KEY&tz_id=Europe/Moscow"
```

