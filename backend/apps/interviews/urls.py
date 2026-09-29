from django.urls import path
from .views import (
    InterviewStartView,
    InterviewListView,
    InterviewDetailView,
    InterviewRespondView,
    InterviewCodeView,
    InterviewEndView,
    InterviewFeedbackView,
)

urlpatterns = [
    path('start/', InterviewStartView.as_view(), name='interview-start'),
    path('', InterviewListView.as_view(), name='interview-list'),
    path('<int:session_id>/', InterviewDetailView.as_view(), name='interview-detail'),
    path('<int:session_id>/respond/', InterviewRespondView.as_view(), name='interview-respond'),
    path('<int:session_id>/code/', InterviewCodeView.as_view(), name='interview-code'),
    path('<int:session_id>/end/', InterviewEndView.as_view(), name='interview-end'),
    path('<int:session_id>/feedback/', InterviewFeedbackView.as_view(), name='interview-feedback'),
]
