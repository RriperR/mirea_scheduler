#!/bin/sh

# Ожидаем, пока БД поднимется
echo "Ожидание базы данных..."
while ! nc -z db 5432; do
  sleep 1
done
echo "База данных доступна!"

# Применяем миграции
python manage.py migrate

# Запускаем Django
python manage.py runserver 0.0.0.0:8000
