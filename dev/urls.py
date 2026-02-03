from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth import views as auth_views
from shortener.views import password_reset_otp_request, verify_otp

schema_view = get_schema_view(
    openapi.Info(
        title="URL Shortener API",
        default_version="v1",
        description="API documentation for the URL shortener",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include('allauth.urls')),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/token/", TokenObtainPairView.as_view()),
    # OTP-based password reset
    path("password-reset-otp/", password_reset_otp_request, name="password_reset_otp_request"),
    path("verify-otp/<str:email>/", verify_otp, name="verify_otp"),
    path("", include("shortener.urls")),
]
