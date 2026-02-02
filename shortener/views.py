import random
import string

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ShortURL



def generate_short_code(length=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


#web views for registration, login, logout
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not User.objects.filter(username=username).exists():
            User.objects.create_user(username=username, password=password)
            return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    urls = ShortURL.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "dashboard.html", {"urls": urls})


@login_required
def create_url(request):
    if request.method == "POST":
        original_url = request.POST.get("url")

        ShortURL.objects.create(
            user=request.user,
            original_url=original_url,
            short_code=generate_short_code()
        )

        return redirect("dashboard")

    return render(request, "create_url.html")


def redirect_url(request, code):
    url = get_object_or_404(ShortURL, short_code=code)
    url.clicks += 1
    url.save()
    return HttpResponseRedirect(url.original_url)


#Api views for registration and URL CRUD
@api_view(["POST"])
def api_register(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    User.objects.create_user(username=username, password=password)
    return Response({"message": "User registered successfully"}, status=201)



@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
def api_urls(request):
    """
    POST  -> Create short URL
    GET   -> List user's URLs
    """

    if request.method == "POST":
        original_url = request.data.get("url")

        short = ShortURL.objects.create(
            user=request.user,
            original_url=original_url,
            short_code=generate_short_code()
        )

        return Response({
            "id": short.id,
            "short_code": short.short_code,
            "original_url": short.original_url
        }, status=201)

    if request.method == "GET":
        urls = ShortURL.objects.filter(user=request.user).values(
            "id", "original_url", "short_code", "clicks", "created_at"
        )
        return Response(list(urls))


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def api_url_detail(request, id):
    """
    GET    -> Retrieve single URL
    PUT    -> Update URL
    DELETE -> Delete URL
    """

    url = get_object_or_404(ShortURL, id=id, user=request.user)

    if request.method == "GET":
        return Response({
            "id": url.id,
            "original_url": url.original_url,
            "short_code": url.short_code,
            "clicks": url.clicks,
            "created_at": url.created_at
        })

    if request.method == "PUT":
        url.original_url = request.data.get("url", url.original_url)
        url.save()
        return Response({"message": "URL updated successfully"})

    if request.method == "DELETE":
        url.delete()
        return Response({"message": "URL deleted successfully"})