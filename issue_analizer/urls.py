from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import IssueAPIView, ScheduleProcessingView, TaskStatusView

router = DefaultRouter()

urlpatterns = [
    path('issueslist', IssueAPIView.as_view()),
    path('schedule/process', ScheduleProcessingView.as_view()),  # Запуск обработки
    path('schedule/process/<str:task_id>/', TaskStatusView.as_view()),  # Проверка статуса
]
urlpatterns += router.urls
