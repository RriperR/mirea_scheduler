import redis
import hashlib
from celery.result import AsyncResult

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from django.utils.timezone import now
from django.db import transaction
from django.conf import settings

from .tasks import update_schedule_task
from issue_analizer.models import ScheduleIssue, ScheduleEvent, IssueCategory
from issue_analizer.serializers import IssueSerializer
from issue_analizer.services.schedule_service import ScheduleService
from issue_analizer.services.schedule_analyzer import ScheduleAnalyzer




class IssueAPIView(ListAPIView):
    """API-контроллер для получения списка ошибок в расписании"""
    serializer_class = IssueSerializer

    def get_queryset(self):
        """Перед выдачей данных проверяет их актуальность и обновляет при необходимости"""
        queryset = ScheduleIssue.objects.all()
        group = self.request.query_params.get("group")
        teacher = self.request.query_params.get("teacher")

        if group:
            queryset = queryset.filter(related_event__group__icontains=group)
        if teacher:
            queryset = queryset.filter(related_event__teacher__icontains=teacher)

        return queryset

    def is_data_fresh(self):
        """Проверяет, обновлялись ли данные за последние 24 часа"""
        last_issue = ScheduleIssue.objects.order_by("-last_updated").first()
        return last_issue and (now() - last_issue.last_updated).total_seconds() < 86400  # 24 часа

    def update_schedule(self):
        """Обновляет данные расписания и ошибки в БД"""
        print("🗑 Очищаем старые данные...")
        ScheduleIssue.objects.all().delete()

        # Загружаем расписание
        schedule_data = []
        for schedule in ScheduleService.fetch_schedule():
            schedule_data.extend(ScheduleService.fetch_ical(schedule["iCalLink"]))

        # Анализируем неудобства
        issues = ScheduleAnalyzer.find_issues(schedule_data)

        # Сохраняем в БД
        with transaction.atomic():
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

                # 🔹 Создаём запись об ошибке и привязываем оба события
                issue_obj = ScheduleIssue.objects.create(
                    issue_type=category,
                    related_event=related_event,
                    related_event_2=related_event_2,
                    description=truncate_text(issue["description"], 255),
                    last_updated=now()
                )


def truncate_text(text, max_length=255):
    text = str(text)
    if len(text) > max_length:
        return text[:max_length]
    return text


# Подключаем Redis
redis_client = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)


class ScheduleProcessingView(APIView):
    """API для запуска фоновой обработки расписания с очередью и уникальными запросами"""

    REDIS_ACTIVE_TASK_KEY = "active_schedule_task"
    REDIS_QUERY_HASH_KEY = "query_task_map"

    def post(self, request):
        """Запускаем обработку расписания (с управлением очередью и учётом параметров)"""

        # Получаем query параметры
        group = request.query_params.get("group", "")
        teacher = request.query_params.get("teacher", "")

        # Формируем уникальный ключ для запроса
        query_string = f"group={group}&teacher={teacher}"
        query_hash = hashlib.md5(query_string.encode()).hexdigest()

        # Проверяем, есть ли уже активная задача
        active_task_id = redis_client.get(self.REDIS_ACTIVE_TASK_KEY)

        if active_task_id:
            task_result = AsyncResult(active_task_id)

            if task_result.state in ["PENDING", "STARTED"]:
                # Проверяем, есть ли уже созданный task_id для этого запроса
                existing_task_id = redis_client.hget(self.REDIS_QUERY_HASH_KEY, query_hash)
                if existing_task_id:
                    return Response({
                        "task_id": existing_task_id,
                        "status": "IN_QUEUE"
                    }, status=202)

        # Если новый запрос, создаём новую задачу
        task = update_schedule_task.delay(group=group, teacher=teacher)

        # Сохраняем новую задачу в Redis
        redis_client.set(self.REDIS_ACTIVE_TASK_KEY, task.id, ex=3600)  # 1 час TTL
        redis_client.hset(self.REDIS_QUERY_HASH_KEY, query_hash, task.id)  # Привязываем параметры к task_id

        return Response({"task_id": task.id, "status": "STARTED"}, status=201)

    def get(self, request):
        """Проверяем статус задачи"""

        task_id = redis_client.get(self.REDIS_ACTIVE_TASK_KEY)
        if not task_id:
            return Response({"status": "NO_ACTIVE_TASK"}, status=404)

        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})


class TaskStatusView(APIView):
    """API для получения статуса Celery-задачи"""
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})
