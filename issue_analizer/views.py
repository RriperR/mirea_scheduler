from .tasks import update_schedule_task
from issue_analizer.models import ScheduleIssue, ScheduleEvent, IssueCategory
from issue_analizer.serializers import IssueSerializer
from issue_analizer.services.schedule_service import ScheduleService
from issue_analizer.services.schedule_analyzer import ScheduleAnalyzer

from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response

from celery.result import AsyncResult

from django.utils.timezone import now
from django.db import transaction


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



class ScheduleProcessingView(APIView):
    """API для запуска фоновой обработки расписания"""
    def post(self, request):
        """Запуск фонового обновления"""
        group = request.query_params.get("group")
        teacher = request.query_params.get("teacher")

        task = update_schedule_task.delay(group=group, teacher=teacher)
        return Response({"task_id": task.id}, status=201)


class TaskStatusView(APIView):
    """API для получения статуса Celery-задачи"""
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        return Response({"task_id": task_id, "status": result.status, "result": result.result})
