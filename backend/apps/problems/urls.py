from django.urls import path
from apps.problems.views import ProblemListView, ProblemDetailView

urlpatterns = [
    path('', ProblemListView.as_view(), name='problem-list'),
    path('<slug:slug>/', ProblemDetailView.as_view(), name='problem-detail'),
]
