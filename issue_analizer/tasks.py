import redis
import hashlib
from celery import shared_task
from django.utils.timezone import now
from django.db import transaction
from django.conf import settings

from .models import ScheduleIssue, ScheduleEvent, IssueCategory
from .services.schedule_service import ScheduleService
from .services.schedule_analyzer import ScheduleAnalyzer
from issue_analizer.serializers import IssueSerializer

# Подключаем Redis
redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)

# Ключи в Redis
REDIS_ACTIVE_TASK_KEY = "active_schedule_task"
REDIS_QUERY_HASH_KEY = "query_task_map"


@shared_task(bind=True)
def update_schedule_task(self, group=None, teacher=None):
    """Фоновая задача обновления расписания с безопасным обновлением БД"""

    # Формируем уникальный ключ запроса
    query_string = f"group={group}&teacher={teacher}"
    query_hash = hashlib.md5(query_string.encode()).hexdigest()

    print(f"🔄 Начало обработки запроса: {query_string}")

    try:
        print("📥 Загружаем новые данные...")
        new_issues = []  # Список новых записей

        # Загружаем расписание
        schedule_data = []
        for schedule in ScheduleService.fetch_schedule():
            schedule_data.extend(ScheduleService.fetch_ical(schedule["iCalLink"]))

        # Анализируем неудобства
        issues = ScheduleAnalyzer.find_issues(schedule_data)

        # Готовим новые объекты (но пока не сохраняем)
        for issue in issues:
            category, _ = IssueCategory.objects.get_or_create(name=issue["category"])

            related_event = ScheduleEvent.objects.create(
                summary=truncate_text(issue["summary"], 255),
                start_time=issue["start"],
                end_time=issue["end"],
                location=truncate_text(issue["location"], 255),
                teacher=truncate_text(issue["teacher"], 255),
                group=truncate_text(issue["group"], 255),
                discipline=truncate_text(issue["discipline"], 255),
            )

            related_event_2 = ScheduleEvent.objects.create(
                summary=truncate_text(issue["related_summary_2"], 255),
                start_time=issue["related_start_2"],
                end_time=issue["related_end_2"],
                location=truncate_text(issue["related_location_2"], 255),
                teacher=truncate_text(issue["related_teacher_2"], 255),
                group=truncate_text(issue["related_group_2"], 255),
                discipline=truncate_text(issue["related_discipline_2"], 255),
            )

            new_issues.append(ScheduleIssue(
                issue_type=category,
                related_event=related_event,
                related_event_2=related_event_2,
                description=truncate_text(issue["description"], 255),
                last_updated=now()
            ))

        #  Безопасное обновление БД
        with transaction.atomic():
            temp_issues = ScheduleIssue.objects.bulk_create(new_issues)  # Создаём новые данные
            if temp_issues:  # Если новые данные успешно добавлены
                ScheduleIssue.objects.exclude(id__in=[issue.id for issue in temp_issues]).delete()  # Удаляем старые
            else:
                print("⚠️ Новые данные не загружены, старые не удаляем!")

        print("✅ База данных обновлена!")

        # Фильтрация по параметрам
        print(f"🔎 Всего записей в БД перед фильтрацией: {ScheduleIssue.objects.count()}")
        queryset = ScheduleIssue.objects.all()

        if group:
            queryset = queryset.filter(related_event__group__icontains=group)
            print(f"🔎 После фильтрации по группе ({group}): {queryset.count()} записей")

        if teacher:
            queryset = queryset.filter(related_event__teacher__icontains=teacher)
            print(f"🔎 После фильтрации по преподавателю ({teacher}): {queryset.count()} записей")

        if queryset.count() == 0:
            print("⚠️ Внимание: после фильтрации данных не осталось!")

        result_data = IssueSerializer(queryset, many=True).data
        print("✅ Запрос обработан успешно.")

        return result_data

    except Exception as e:
        print(f"❌ Ошибка во время обработки запроса: {e}")
        raise

    finally:
        # Очистка Redis после выполнения задачи
        redis_client.delete(REDIS_ACTIVE_TASK_KEY)
        redis_client.hdel(REDIS_QUERY_HASH_KEY, query_hash)

        print(f"🗑 Очистка Redis после завершения задачи: {query_string}")

def truncate_text(text, max_length=255):
    text = str(text)
    if len(text) > max_length:
        return text[:max_length]
    return text
