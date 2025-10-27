# Microblog API

Бэкенд корпоративного сервиса микроблогов со скачиваемым фронтендом и документацией через Swagger.

## Возможности
- Создание, удаление и просмотр твитов с поддержкой изображений.
- Лента твитов от фолловингов, отсортированная по популярности (количество лайков → ID).
- Лайки, анлайки и управление фолловерами.
- Публичные профили и эндпоинт для текущего пользователя.
- Хранилище медиафайлов и отдача статики (директория `media/` и собранный фронт `dist/`).
- Swagger/UI доступен на `http://localhost:8000/docs`.

## Быстрый старт (Docker)
```bash
cp .env.example .env
docker-compose up -d --build
```
- API доступно по адресу `http://localhost:8000`.
- Документация: `http://localhost:8000/docs`.
- Для авторизации используйте заголовок `api-key`. В демонстрационных данных присутствуют ключи `test`, `alice`, `bob`.

## Запуск без Docker
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://microblog:microblog@localhost:5432/microblog"
alembic upgrade head
uvicorn app.main:app --reload
```

## Тесты и качество кода
```bash
APP_SKIP_BOOTSTRAP=1 pytest
```
Перед запуском тестов переменная `APP_SKIP_BOOTSTRAP` отключает автоматический сидинг продовой БД.

### Проверка форматирования
```bash
black app tests
```
Форматирование контролируется в CI (`black --check`), используем конфигурацию из `pyproject.toml` с длиной строки 120 символов.

## CI
Репозиторий содержит workflow `.github/workflows/ci.yml`, который при каждом push/PR выполняет:
- проверку форматирования `black --check app tests`;
- тесты `pytest` с `APP_SKIP_BOOTSTRAP=1`.

## Основные эндпоинты
- `POST /api/medias` — загрузка медиафайла (form-data, поле `file`).
- `POST /api/tweets` — создание твита (опционально `tweet_media_ids`).
- `DELETE /api/tweets/{tweet_id}` — удаление собственного твита.
- `POST /api/tweets/{tweet_id}/likes` / `DELETE /api/tweets/{tweet_id}/likes` — управление лайками.
- `GET /api/tweets` — популярная лента фолловингов.
- `POST /api/users/{user_id}/follow` / `DELETE /api/users/{user_id}/follow` — подписки.
- `GET /api/users/me` — профиль текущего пользователя.
- `GET /api/users/{user_id}` — публичный профиль.
- `GET /api/users` — список пользователей с флагом подписки и счётчиками.
- `GET /api/users/{user_id}/followers` — список читателей.
- `GET /api/users/{user_id}/following` — список читаемых.

Все ответы имеют вид:
```json
{ "result": true, "...": "..." }
```
или в случае ошибки:
```json
{ "result": false, "error_type": "...", "error_message": "..." }
```

## Демо-данные
При старте (если не отключено `APP_SKIP_BOOTSTRAP=1`) автоматически создаются пользователи `test`, `alice`, `bob`, несколько твитов, подписки и лайки для проверки UI.
