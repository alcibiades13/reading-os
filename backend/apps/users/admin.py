from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced admin for custom User model"""
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_active', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'bio', 'avatar', 'location', 'website')}),
        ('Reading DNA', {'fields': ('reading_dna',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for user profiles"""
    list_display = ['user', 'is_public', 'reading_goal_year', 'created_at']
    list_filter = ['is_public', 'show_reading_stats', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Privacy', {'fields': ('is_public', 'show_reading_stats', 'show_quotes')}),
        ('Reading Preferences', {'fields': ('reading_goal_year', 'favorite_genres', 'reading_preferences')}),
        ('Notifications', {'fields': ('email_on_friend_request', 'email_on_circle_invite', 'email_on_quote_comment')}),
        ('Metadata', {'fields': ('created_at', 'updated_at')}),
    )

