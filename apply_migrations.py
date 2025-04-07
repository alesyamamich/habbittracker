from app import app, db  # Импортируйте ваше приложение и объект базы данных
from flask_migrate import upgrade

# Инициализация приложения
with app.app_context():
    # Применение миграций
    upgrade()
    print("Миграции успешно применены.")