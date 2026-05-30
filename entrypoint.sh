#!/bin/sh

echo "Waiting for postgres..."

while ! pg_isready -h $DB_HOST -p $DB_PORT -U $POSTGRES_USER -d $POSTGRES_DB; do
  sleep 1
done

echo "PostgreSQL started"

python manage.py migrate
python manage.py seed_data

exec "$@"
