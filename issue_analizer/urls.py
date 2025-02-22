from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import IssueAPIView, ScheduleProcessingView

router = DefaultRouter()

urlpatterns = [
    path('issueslist', IssueAPIView.as_view()),
    path('schedule/process', ScheduleProcessingView.as_view()),  # Запуск обработки
]
urlpatterns += router.urls
