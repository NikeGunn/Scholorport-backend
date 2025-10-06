#!/bin/bash
set -e

echo "🚀 Scholarport Backend Starting..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready!"

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Load university data if needed
if [ ! -f /app/.universities_loaded ]; then
    echo "🏫 Loading university data..."
    python manage.py load_universities && touch /app/.universities_loaded
fi

# Start the application
echo "✅ Starting Gunicorn..."
exec "$@"
