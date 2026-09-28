from django.contrib import admin
from apps.problems.models import Problem

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'difficulty', 'slug', 'topics_display', 'created_at')
    list_filter = ('difficulty',)
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('id',)

    def topics_display(self, obj):
        return ", ".join(obj.topics or [])
    topics_display.short_description = 'Topics'
