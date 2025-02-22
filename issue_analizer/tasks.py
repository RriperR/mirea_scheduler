from celery import shared_task
import time

@shared_task
def process_schedule():
    """Фоновая задача для обработки расписания"""
    time.sleep(10)  # Симуляция долгой обработки
    return {"status": "Готово", "data": "Здесь будут данные"}
