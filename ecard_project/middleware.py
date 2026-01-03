from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
import time


class SessionExpiryMiddleware(MiddlewareMixin):
    """
    Middleware to handle session expiration and redirect users to home page
    when their session expires or when they're not authenticated for protected URLs.
    """
    
    def process_request(self, request):
        # Define protected URLs that require authentication
        protected_urls = [
            reverse('dashboard'),
            reverse('bluetooth_sync'),
            reverse('sync_to_badge'),
        ]
        
        # Check if the current path is a protected URL
        if request.path in protected_urls and not request.user.is_authenticated:
            return redirect('home')
        
        # Check if user is authenticated but session may have expired
        if request.user.is_authenticated:
            # Optional: Implement custom session timeout logic here if needed
            # For now, we just ensure authenticated users can access protected URLs
            pass
        
        return None
