from django.contrib import admin
from apps.progress.models import UserProblemProgress

@admin.register(UserProblemProgress)
class UserProblemProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'problem', 'status', 'attempts', 'time_spent', 'solved_at')
    list_filter = ('status', 'solved_at')
    search_fields = ('user__email', 'problem__title', 'problem__slug')
    ordering = ('-id',)
