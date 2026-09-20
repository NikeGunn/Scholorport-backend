#!/bin/bash
set -e

echo "🚀 Scholarport Backend Starting..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
# Use defaults if env vars not set
: ${POSTGRES_HOST:=db}
: ${POSTGRES_PORT:=5432}
: ${POSTGRES_USER:=postgres}
: ${POSTGRES_DB:=postgres}

# -d must be explicit: pg_isready defaults -d to $POSTGRES_USER when omitted,
# which probes a database that doesn't exist and spams FATAL logs on the db side.
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB > /dev/null 2>&1; do
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
