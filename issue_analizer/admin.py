from django.contrib import admin

from .models import IssueCategory, ScheduleIssue, ScheduleEvent

admin.site.register(IssueCategory)
admin.site.register(ScheduleIssue)
admin.site.register(ScheduleEvent)