from django.utils.timezone import now
from django.db import models

class IssueCategory(models.Model):
    """Категория ошибки (тип найденной проблемы)"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class ScheduleEvent(models.Model):
    """Занятие из расписания"""
    summary = models.CharField(max_length=255)  # Название предмета
    start_time = models.DateTimeField()  # Время начала
    end_time = models.DateTimeField()  # Время окончания
    location = models.CharField(max_length=255)  # Аудитория
    teacher = models.CharField(max_length=255, blank=True, null=True)  # Преподаватель
    group = models.CharField(max_length=255)  # Название группы
    discipline = models.CharField(max_length=255)  # Дисциплина

    def __str__(self):
        return f"{self.summary} ({self.group}) - {self.start_time}"


class ScheduleIssue(models.Model):
    """Ошибка в расписании"""
    issue_type = models.ForeignKey(IssueCategory, on_delete=models.CASCADE)  # Тип ошибки
    related_event = models.ForeignKey(ScheduleEvent, on_delete=models.CASCADE, related_name="related_event")  # Занятие, связанное с проблемой
    related_event_2 = models.ForeignKey(ScheduleEvent, on_delete=models.CASCADE, related_name="related_event_2")  # Второе занятие
    description = models.TextField(blank=True)  # Описание проблемы
    detected_at = models.DateTimeField(auto_now_add=True)  # Когда обнаружена ошибка
    last_updated = models.DateTimeField(default=now) # Дата последнего обновления

    def __str__(self):
        return f"{self.issue_type} - {self.description}"
