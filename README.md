# 🍳 Foodgram - Рецепты и кулинарные идеи

![Workflow Status](https://github.com/GoodWinee/foodgram/actions/workflows/main.yml/badge.svg)

**Foodgram** — это современный веб-сайт для публикации и обмена кулинарными рецептами. Пользователи могут создавать свои рецепты, подписываться на авторов, добавлять рецепты в избранное и создавать список покупок.

## 📱 Основные функции

- Регистрация и вход - создание аккаунта и безопасная аутентификация
- Публикация рецептов - добавление новых рецептов с изображениями
- Поиск и фильтрация - по тегам, авторам и другим параметрам
- Избранное - сохранение любимых рецептов
- Список покупок - сбор ингредиентов для выбранных рецептов
- Подписки - следите за любимыми авторами
- Скачивание списка покупок - получение готового списка для покупок

Проект разработан с использованием современных технологий и лучших практик разработки, включая контейнеризацию, CI/CD и автоматическое тестирование.

## 🛠️ Стек технологий

### Бэкенд
- **Python 3.12** — язык программирования
- **Django 3.2+** — веб-фреймворк
- **Django REST Framework** — создание REST API
- **Djoser** — аутентификация через токены
- **PostgreSQL 13** — база данных
- **Gunicorn** — WSGI-сервер

### Фронтенд
- **React** — библиотека для создания пользовательского интерфейса
- **JavaScript/TypeScript** — язык программирования
- **HTML5/CSS3** — разметка и стилизация

### Инфраструктура
- **Docker** — контейнеризация приложения
- **Docker Compose** — оркестрация контейнеров
- **Nginx** — веб-сервер и обратный прокси
- **GitHub Actions** — CI/CD пайплайн
- **Let's Encrypt** — SSL сертификаты

## 🚀 Развертывание проекта

### Требования

- Docker 20.10+
- Docker Compose 2.0+
- Git
- Доменное имя (опционально для SSL)

### Быстрый старт

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/GoodWinee/foodgram
   cd foodgram
2. **Создайте файл .env в корне проекта:**
   ```bash
   cp .env.example .env
3. **Заполните переменные окружения.**
4. **Запустите проект:**
   ```bash
   docker compose -f docker-compose.production.yml up -d --build
5. **Примените миграции и соберите статику:**
   ```bash
   docker compose -f docker-compose.production.yml exec backend python manage.py migrate
   docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
6. **Заполните базу данных ингредиентами (опционально)**
   ```bash
   docker compose -f docker-compose.production.yml exec backend python manage.py filldb
7. **Откройте приложение в браузере:**
   - 🌐 Фронтенд: `http://localhost:8080`
   - 🔐 Админка: `http://localhost:8080/admin/`

## 📡 API Endpoints
### Основные эндпоинты API:
- Регистрация: POST /api/users/
- Вход: POST /api/auth/token/login/
- Рецепты: GET /api/recipes/
- Избранное: POST /api/recipes/{id}/favorite/
- Список покупок: POST /api/recipes/{id}/shopping_cart/
- Подписки: GET /api/users/subscriptions/
- Документация API /api/docs/

## Автор

**GoodWinee** — разработчик проекта

- **GitHub:** [@GoodWinee](https://github.com/GoodWinee)
- **Репозиторий:** [https://github.com/GoodWinee/foodgram](https://github.com/GoodWinee/foodgram)
- **Демо:** [https://ffoodgram.ddns.net](https://ffoodgram.ddns.net)
- **API Docs** [https://ffoodgram.ddns.net/api/docs](https://ffoodgram.ddns.net/api/docs)

---

**Счастливого кодинга! 🚀**
