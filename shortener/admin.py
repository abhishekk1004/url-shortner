from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import ShortURL, UserProfile

# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fields = ('full_name', 'phone')

# Extended User Admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_full_name', 'get_phone', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'userprofile__full_name', 'userprofile__phone')
    
    def get_full_name(self, obj):
        try:
            return obj.userprofile.full_name
        except:
            return '-'
    get_full_name.short_description = 'Full Name'
    
    def get_phone(self, obj):
        try:
            return obj.userprofile.phone
        except:
            return '-'
    get_phone.short_description = 'Phone'

# Unregister the default User admin and register custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'phone')
    search_fields = ('full_name', 'phone', 'user__username', 'user__email')
    list_filter = ('user__date_joined',)

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
