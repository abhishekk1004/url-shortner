from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("create/", views.create_url, name="create"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("<str:code>/", views.redirect_url, name="redirect"),
    path("api/register/", views.api_register, name="api_register"),
    path("api/urls/", views.api_urls, name="api_urls"),
    path("api/urls/<int:id>/", views.api_url_detail, name="api_url_detail"),
]
