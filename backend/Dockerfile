FROM php:8.3-fpm-alpine AS base

# Install PHP extensions
# NOTE: Using SQLite temporarily for development. Minimal deps only.
# For production: add postgresql-dev and install pdo_pgsql instead.
RUN apk add --no-cache sqlite-dev oniguruma-dev curl \
    && docker-php-ext-install pdo pdo_sqlite mbstring bcmath

# Install Composer
COPY --from=composer:2.7 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Install Laravel and dependencies
COPY composer.json composer.lock* ./
RUN composer install --no-dev --optimize-autoloader --no-interaction

COPY . .

RUN chown -R www-data:www-data storage bootstrap/cache database \
    && chmod -R 775 storage bootstrap/cache database

# Create the SQLite file if it doesn't exist, migrate, seed, then serve
EXPOSE 8080
CMD ["sh", "-c", "touch database/database.sqlite && php artisan migrate --force && php artisan db:seed --force && php artisan serve --host=0.0.0.0 --port=8080"]
