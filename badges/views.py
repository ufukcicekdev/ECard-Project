from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.contrib.auth.forms import AuthenticationForm
from .models import BadgeProfile, SocialMediaLink


def public_profile(request, slug):
    """Display the public profile page for a user"""
    badge_profile = get_object_or_404(BadgeProfile, slug=slug)
    context = {
        'profile': badge_profile,
    }
    return render(request, 'badges/public_profile.html', context)


@login_required
def dashboard(request):
    """Dashboard for logged-in users to edit their profile"""
    try:
        profile = request.user.badgeprofile
    except BadgeProfile.DoesNotExist:
        profile = BadgeProfile.objects.create(user=request.user, full_name=request.user.get_full_name() or request.user.username)
    
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', profile.full_name)
        profile.job_title = request.POST.get('job_title', profile.job_title)
        profile.description = request.POST.get('description', profile.description)
        profile.email = request.POST.get('email', profile.email)
        profile.phone_number = request.POST.get('phone', profile.phone_number)
        

        
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']
        else:
            # Check if a file was selected but not processed
            if request.method == 'POST':
                # Check if the profile_image field exists in the form
                profile_image_field = request.POST.get('profile_image')
                if profile_image_field:
                    print(f"profile_image field exists in POST: {profile_image_field}")
                else:
                    print("profile_image field does not exist in POST")
        
        

        profile.save()
        
        # Handle social media links
        # Get all platform keys to identify which links should exist
        platform_keys = [key for key in request.POST.keys() if key.startswith('platform_')]
        
        # Create a list of link IDs that are currently in the form
        current_link_ids = []
        for platform_key in platform_keys:
            platform_index = platform_key.split('_')[1]
            link_id = request.POST.get(f'link_id_{platform_index}')
            if link_id:
                current_link_ids.append(link_id)
        
        # Delete links that are not in the current form (i.e., were removed by user)
        links_to_delete = profile.social_links.exclude(id__in=current_link_ids)
        links_to_delete.delete()
        
        # Add/update social media links
        for platform_key in platform_keys:
            platform_index = platform_key.split('_')[1]
            platform_value = request.POST.get(platform_key)
            url_value = request.POST.get(f'url_{platform_index}')
            
            if platform_value and url_value:
                # Update existing or create new
                link_id = request.POST.get(f'link_id_{platform_index}')
                if link_id:
                    try:
                        link = profile.social_links.get(id=link_id)
                        link.platform = platform_value
                        link.url = url_value
                        link.save()
                    except SocialMediaLink.DoesNotExist:
                        SocialMediaLink.objects.create(
                            profile=profile, 
                            platform=platform_value, 
                            url=url_value
                        )
                else:
                    SocialMediaLink.objects.create(
                        profile=profile, 
                        platform=platform_value, 
                        url=url_value
                    )
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('dashboard')
    
    context = {
        'profile': profile,
    }
    return render(request, 'badges/dashboard.html', context)


@login_required
def bluetooth_sync(request):
    """Page with Bluetooth sync functionality"""
    try:
        profile = request.user.badgeprofile
    except BadgeProfile.DoesNotExist:
        profile = BadgeProfile.objects.create(user=request.user, full_name=request.user.get_full_name() or request.user.username)
    
    context = {
        'profile': profile,
    }
    return render(request, 'badges/bluetooth_sync.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def sync_to_badge(request):
    """API endpoint to sync profile data to the badge via Bluetooth"""
    try:
        profile = request.user.badgeprofile
        data_string = f"{profile.full_name}|{profile.job_title}|{request.build_absolute_uri('/p/' + profile.slug)}"
        
        # In a real implementation, this would send data to the ESP32-C3 via Bluetooth
        # For now, we'll just return a success response
        return JsonResponse({'success': True, 'data': data_string})
    except BadgeProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a default badge profile for the user
            BadgeProfile.objects.create(
                user=user,
                full_name=user.username,
                job_title='New User'
            )
            # Log the user in after registration
            login(request, user)
            messages.success(request, 'Registration successful! You can now update your profile.')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@csrf_exempt
def login_view(request):
    """Custom login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                # Redirect to dashboard after successful login
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


def register_view(request):
    """Custom register view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a default badge profile for the user
            BadgeProfile.objects.create(
                user=user,
                full_name=user.username,
                job_title='New User'
            )
            # Authenticate and log the user in after registration
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to your dashboard.')
                return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


from django.contrib.auth import logout


def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')


def home(request):
    """Home page view"""
    return render(request, 'home.html')


def contact(request):
    """Contact page view"""
    return render(request, 'contact.html')


def custom_404_view(request, exception):
    """Custom 404 error page"""
    return render(request, '404.html', status=404)


def custom_500_view(request):
    """Custom 500 error page"""
    return render(request, '500.html', status=500)
