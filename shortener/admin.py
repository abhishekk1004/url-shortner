from django.contrib import admin
from .models import ShortURL

@admin.register(ShortURL)
class ShortURLAdmin(admin.ModelAdmin):
    list_display = (
        "short_key",
        "original_url",
        "user",
        "clicks",
        "created_at",
        "expires_at",
    )

    search_fields = ("short_key", "original_url", "user__username")
    list_filter = ("created_at", "expires_at")
    ordering = ("-created_at",)

    readonly_fields = ("clicks", "created_at")

    fieldsets = (
        ("URL Info", {
            "fields": ("original_url", "short_key")
        }),
        ("Ownership", {
            "fields": ("user",)
        }),
        ("Analytics", {
            "fields": ("clicks",)
        }),
        ("Expiration", {
            "fields": ("expires_at",)
        }),
    )
