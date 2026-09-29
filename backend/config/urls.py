from django.contrib import admin
from django.urls import path, include
from apps.submissions.views import AnalyticsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/problems/', include('apps.problems.urls')),
    path('api/progress/', include('apps.progress.urls')),
    path('api/submissions/', include('apps.submissions.urls')),
    path('api/coaching/', include('apps.coaching.urls')),
    path('api/analytics/', AnalyticsView.as_view(), name='analytics-dashboard'),
]
