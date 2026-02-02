from django.db import models
from django.contrib.auth.models import User
import pyotp

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, unique=True)
    full_name = models.CharField(max_length=100)
    
    # 2FA Fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    backup_codes = models.TextField(blank=True, null=True)  # Store as JSON

    def __str__(self):
        return self.full_name
    
    def get_totp(self):
        """Get TOTP object for 2FA verification"""
        if self.two_factor_secret:
            return pyotp.TOTP(self.two_factor_secret)
        return None
    
    def generate_backup_codes(self, count=10):
        """Generate backup codes for recovery"""
        import json
        codes = [pyotp.random_base32()[:8] for _ in range(count)]
        self.backup_codes = json.dumps(codes)
        return codes

class ShortURL(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_url = models.URLField()
    short_key = models.CharField(max_length=20, unique=True)
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.short_key
