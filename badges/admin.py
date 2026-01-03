from django.contrib import admin

from django.contrib import admin
from .models import BadgeProfile, SocialMediaLink


@admin.register(BadgeProfile)
class BadgeProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'job_title', 'user', 'slug')
    list_filter = ('job_title',)
    search_fields = ('full_name', 'job_title', 'user__username', 'user__email')
    prepopulated_fields = {'slug': ('full_name',)}


@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(admin.ModelAdmin):
    list_display = ('profile', 'platform', 'url')
    list_filter = ('platform',)
    search_fields = ('profile__full_name', 'url')
