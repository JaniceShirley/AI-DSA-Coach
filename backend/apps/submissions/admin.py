from django.contrib import admin
from apps.submissions.models import Submission
from apps.problems.models import TestCase

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'problem', 'status', 'test_cases_passed', 'total_test_cases', 'runtime', 'created_at')
    list_filter = ('status', 'language', 'created_at')
    search_fields = ('user__email', 'problem__title', 'problem__slug')
    ordering = ('-created_at',)

@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'problem', 'is_public', 'input_preview', 'created_at')
    list_filter = ('is_public', 'problem__difficulty')
    search_fields = ('problem__title', 'problem__slug', 'input_data', 'expected_output')

    def input_preview(self, obj):
        return obj.input_data[:50] + "..." if len(obj.input_data) > 50 else obj.input_data
    input_preview.short_description = 'Input'
