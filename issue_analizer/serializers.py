from rest_framework import serializers

from issue_analizer.models import ScheduleIssue, ScheduleEvent


class EventSerializer(serializers.ModelSerializer):
    """Сериализатор для событий расписания"""
    class Meta:
        model = ScheduleEvent
        fields = ("id", "summary", "start_time", "end_time", "location", "teacher", "group", "discipline")

class IssueSerializer(serializers.ModelSerializer):
    """Сериализатор для проблем в расписании"""
    issue_type = serializers.CharField(source="issue_type.name")  # Показываем имя категории
    related_event = EventSerializer()  # Вкладываем информацию о первом событии
    related_event_2 = EventSerializer()

    class Meta:
        model = ScheduleIssue
        fields = ("id", "issue_type", "description", "detected_at", "related_event", "related_event_2")

