from django.urls import path
from .views import (
    ChatView,
    SessionStateView,
    SessionResetView,
    HintView,
    ChallengeView,
    AlternativeView,
    FeedbackView,
    HistoryView,
    CoachModeView
)

urlpatterns = [
    path('chat/', ChatView.as_view(), name='coaching-chat'),
    path('session/<int:problem_id>/', SessionStateView.as_view(), name='coaching-session-state'),
    path('session/<int:problem_id>/reset/', SessionResetView.as_view(), name='coaching-session-reset'),
    path('hint/', HintView.as_view(), name='coaching-hint'),
    path('challenge/', ChallengeView.as_view(), name='coaching-challenge'),
    path('alternative/', AlternativeView.as_view(), name='coaching-alternative'),
    path('feedback/', FeedbackView.as_view(), name='coaching-feedback'),
    path('history/<int:problem_id>/', HistoryView.as_view(), name='coaching-history'),
    path('mode/', CoachModeView.as_view(), name='coaching-mode'),
]
