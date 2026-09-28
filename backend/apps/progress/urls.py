from django.urls import path
from apps.progress.views import DashboardProgressView, ProblemProgressDetailView

urlpatterns = [
    path('', DashboardProgressView.as_view(), name='dashboard-progress'),
    path('<int:problem_id>/', ProblemProgressDetailView.as_view(), name='problem-progress-detail'),
]
