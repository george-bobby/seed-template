#!/bin/bash
# TODO: Customize this entrypoint script for your application
# This is an example entrypoint - replace with your application's setup logic

set -e

echo "Starting application container..."

# TODO: Add your application-specific setup steps here
# Examples:
# - Clone application code if not present
# - Install dependencies
# - Set up configuration files
# - Run database migrations
# - Set file permissions

# Example: Create required directories
mkdir -p /var/www/public/attachments /var/www/public/temp

# Example: Install dependencies if needed
if [ ! -d "/var/www/public/vendor" ]; then
    echo "Vendor directory not found, installing dependencies..."
    cd /var/www/public
    # TODO: Replace with your dependency installation command
    # timeout 300 composer install --no-dev --optimize-autoloader --no-interaction || {
    #     echo "ERROR: Dependency installation failed"
    #     exit 1
    # }
fi

# Example: Set permissions
chmod -R 755 /var/www/public
find /var/www/public -type f -exec chmod 644 {} \;

# TODO: Replace with your application's startup command
echo "Starting application server..."
exec php-fpm
