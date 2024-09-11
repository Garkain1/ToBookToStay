#!/bin/sh

DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-3306}

echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Database is up - performing migrations..."

output=$(python manage.py makemigrations)

if echo "$output" | grep -q "No changes detected"; then
  echo "No changes detected - skipping migrate"
else
  echo "Changes detected - running migrate"
  python manage.py migrate
fi

echo "Migrations completed - executing command"

exec "$@"