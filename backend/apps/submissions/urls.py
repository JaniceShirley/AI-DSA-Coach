from django.urls import path
from apps.submissions.views import (
    RunCodeView,
    SubmitCodeView,
    SubmissionListView,
    SubmissionDetailView,
    AnalyticsView
)

urlpatterns = [
    path('run/', RunCodeView.as_view(), name='submission-run'),
    path('submit/', SubmitCodeView.as_view(), name='submission-submit'),
    path('', SubmissionListView.as_view(), name='submission-list'),
    path('<int:submission_id>/', SubmissionDetailView.as_view(), name='submission-detail'),
]
