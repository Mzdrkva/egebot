# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только requirements и сразу ставим зависимости
COPY requirements.txt .
# Обновляем pip и ставим зависимости
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Запуск бота
CMD ["python", "bot.py"]
