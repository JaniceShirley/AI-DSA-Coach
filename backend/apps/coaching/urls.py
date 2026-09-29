from django.urls import path
from .views import HintView, ChallengeView, AlternativeView, FeedbackView, HistoryView

urlpatterns = [
    path('hint/', HintView.as_view(), name='coaching-hint'),
    path('challenge/', ChallengeView.as_view(), name='coaching-challenge'),
    path('alternative/', AlternativeView.as_view(), name='coaching-alternative'),
    path('feedback/', FeedbackView.as_view(), name='coaching-feedback'),
    path('history/<int:problem_id>/', HistoryView.as_view(), name='coaching-history'),
]
