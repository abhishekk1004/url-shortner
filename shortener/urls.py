from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create/", views.create_url, name="create"),
    path("edit/<int:id>/", views.edit_url, name="edit"),
    path("delete/<int:id>/", views.delete_url, name="delete"),
    path("qr/<int:id>/", views.generate_qr_code, name="qr_code"),
    path("qr/<int:id>/download/", views.download_qr_code, name="download_qr"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("settings/", views.settings_view, name="settings"),
    path("2fa/setup/", views.setup_two_fa, name="setup_2fa"),
    path("2fa/disable/", views.disable_two_fa, name="disable_2fa"),
    path("<str:code>/", views.redirect_url, name="redirect"),
    path("api/register/", views.api_register, name="api_register"),
    path("api/urls/", views.api_urls, name="api_urls"),
    path("api/urls/<int:id>/", views.api_url_detail, name="api_url_detail"),
]
