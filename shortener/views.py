import random
import string
import qrcode
import pyotp
import json
from io import BytesIO
import base64
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ShortURL, UserProfile

def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


def generate_short_code(length=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


#web views for registration, login, logout
def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")

        if not full_name or not username or not email or not phone or not password:
            return render(request, "register.html", {"error": "All fields are required"})

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {"error": "Username already exists"})

        if User.objects.filter(email=email).exists():
            return render(request, "register.html", {"error": "Email already exists"})

        from .models import UserProfile
        if UserProfile.objects.filter(phone=phone).exists():
            return render(request, "register.html", {"error": "Phone number already exists"})

        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, full_name=full_name, phone=phone)
        
        return render(request, "register.html", {"success": "Registered successfully! Please login."})

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        two_fa_code = request.POST.get("two_fa_code")

        user = authenticate(username=username, password=password)
        if user:
            try:
                profile = user.userprofile
                # Check if 2FA is enabled
                if profile.two_factor_enabled:
                    # If no 2FA code provided, show 2FA form
                    if not two_fa_code:
                        request.session['pre_2fa_user_id'] = user.id
                        return render(request, "two_fa_login.html", {"username": username})
                    
                    # Verify 2FA code
                    totp = profile.get_totp()
                    if totp and totp.verify(two_fa_code):
                        # 2FA verified, log them in
                        login(request, user)
                        if 'pre_2fa_user_id' in request.session:
                            del request.session['pre_2fa_user_id']
                        return redirect("dashboard")
                    else:
                        # Check backup codes
                        try:
                            backup_codes = json.loads(profile.backup_codes)
                            if two_fa_code in backup_codes:
                                # Remove used backup code
                                backup_codes.remove(two_fa_code)
                                profile.backup_codes = json.dumps(backup_codes)
                                profile.save()
                                login(request, user)
                                if 'pre_2fa_user_id' in request.session:
                                    del request.session['pre_2fa_user_id']
                                messages.warning(request, "Backup code used. Consider regenerating backup codes.")
                                return redirect("dashboard")
                        except:
                            pass
                        
                        request.session['pre_2fa_user_id'] = user.id
                        return render(request, "two_fa_login.html", {"username": username, "error": "Invalid 2FA code"})
                else:
                    # 2FA not enabled, normal login
                    login(request, user)
                    return redirect("dashboard")
            except UserProfile.DoesNotExist:
                login(request, user)
                return redirect("dashboard")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("home")


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
            short_key=generate_short_code()
        )

        return redirect("dashboard")

    return render(request, "create_url.html")


def redirect_url(request, code):
    url = get_object_or_404(ShortURL, short_key=code)
    url.clicks += 1
    url.save()
    return HttpResponseRedirect(url.original_url)


@login_required
def edit_url(request, id):
    url = get_object_or_404(ShortURL, id=id, user=request.user)
    
    if request.method == "POST":
        url.original_url = request.POST.get("url", url.original_url)
        url.save()
        return redirect("dashboard")
    
    return render(request, "edit_url.html", {"url": url})


@login_required
def delete_url(request, id):
    url = get_object_or_404(ShortURL, id=id, user=request.user)
    url.delete()
    return redirect("dashboard")


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
            short_key=generate_short_code()
        )

        return Response({
            "id": short.id,
            "short_key": short.short_key,
            "original_url": short.original_url
        }, status=201)

    if request.method == "GET":
        urls = ShortURL.objects.filter(user=request.user).values(
            "id", "original_url", "short_key", "clicks", "created_at"
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
            "short_key": url.short_key,
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


@login_required
def generate_qr_code(request, id):
    
    url = get_object_or_404(ShortURL, id=id, user=request.user)
    
    # Build the full shortened URL
    short_url = request.build_absolute_uri(f'/{url.short_key}/')
    
    # Force HTTPS if configured
    if getattr(settings, 'USE_HTTPS', False):
        short_url = short_url.replace('http://', 'https://')
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(short_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return render(request, 'qr_code.html', {
        'url': url,
        'short_url': short_url,
        'qr_code': img_str
    })


@login_required
def download_qr_code(request, id):
    """Download QR code as PNG file"""
    from django.conf import settings
    url = get_object_or_404(ShortURL, id=id, user=request.user)
    
    # Build the full shortened URL
    short_url = request.build_absolute_uri(f'/{url.short_key}/')
    
    # Force HTTPS if configured
    if getattr(settings, 'USE_HTTPS', False):
        short_url = short_url.replace('http://', 'https://')
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(short_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Create response with PNG image
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_code_{url.short_key}.png"'
    img.save(response, 'PNG')
    
    return response


@login_required
def setup_two_fa(request):
    """Setup 2FA for user"""
    profile = request.user.userprofile
    
    if profile.two_factor_enabled:
        messages.warning(request, "2FA is already enabled. Disable it first to set it up again.")
        return redirect("settings")
    
    # Generate new secret if not in session
    if 'temp_2fa_secret' not in request.session:
        secret = pyotp.random_base32()
        request.session['temp_2fa_secret'] = secret
    else:
        secret = request.session['temp_2fa_secret']
    
    # Generate QR code
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(name=request.user.email, issuer_name='URL Shortener')
    
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    if request.method == "POST":
        code = request.POST.get("code")
        if totp.verify(code):
            profile.two_factor_secret = secret
            profile.two_factor_enabled = True
            backup_codes = profile.generate_backup_codes()
            profile.save()
            del request.session['temp_2fa_secret']
            return render(request, "two_fa_backup_codes.html", {"backup_codes": backup_codes})
        else:
            messages.error(request, "Invalid code. Please try again.")
    
    return render(request, "two_fa_setup.html", {
        "qr_code": qr_code_base64,
        "secret": secret,
        "email": request.user.email
    })


@login_required
def disable_two_fa(request):
    """Disable 2FA"""
    profile = request.user.userprofile
    
    if not profile.two_factor_enabled:
        messages.warning(request, "2FA is not enabled.")
        return redirect("settings")
    
    if request.method == "POST":
        code = request.POST.get("code")
        totp = profile.get_totp()
        
        if totp and (totp.verify(code) or code in json.loads(profile.backup_codes or "[]")):
            profile.two_factor_enabled = False
            profile.two_factor_secret = None
            profile.backup_codes = None
            profile.save()
            messages.success(request, "2FA has been disabled.")
            return redirect("settings")
        else:
            messages.error(request, "Invalid code.")
    
    return render(request, "two_fa_disable.html")


@login_required
def settings_view(request):
    """User settings page"""
    profile = request.user.userprofile
    return render(request, "settings.html", {
        "profile": profile,
        "two_fa_enabled": profile.two_factor_enabled
    })