from django.urls import path
from .views import (
    RegisterAPI,
    CreateShortURLAPI,
    ListURLsAPI,
    RedirectAPIView,
    DeleteURLAPI
)

urlpatterns = [
    path("auth/register/", RegisterAPI.as_view()),
    path("urls/", ListURLsAPI.as_view()),
    path("shorten/", CreateShortURLAPI.as_view()),
    path("delete/<str:key>/", DeleteURLAPI.as_view()),
    path("<str:key>/", RedirectAPIView.as_view()),
]
