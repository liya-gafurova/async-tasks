from django.urls import path

from .views import LaunchProcessingApi

urlpatterns = [
    path('', LaunchProcessingApi.as_view(), name='process'),
]