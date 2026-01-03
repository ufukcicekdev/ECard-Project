from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

# Check if we should use custom storage for DigitalOcean Spaces
def get_profile_image_storage():
    try:
        from .storage_backends import MediaStorage
        return MediaStorage()
    except ImportError:
        return None


class SocialMediaLink(models.Model):
    PLATFORM_CHOICES = [
        ('twitter', 'Twitter/X'),
        ('linkedin', 'LinkedIn'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('github', 'GitHub'),
        ('youtube', 'YouTube'),
        ('tiktok', 'TikTok'),
        ('other', 'Other'),
    ]
    
    profile = models.ForeignKey('BadgeProfile', on_delete=models.CASCADE, related_name='social_links')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField(max_length=500)
    
    def __str__(self):
        return f"{self.get_platform_display()} - {self.url}"


class BadgeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200)
    
    # Get the appropriate storage for profile images
    storage = get_profile_image_storage()
    if storage:
        profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True, storage=storage)
    else:
        profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    
    description = models.TextField(max_length=2500, blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.full_name + "-" + str(self.user.id))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.full_name} - {self.job_title}"