from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('p/<slug:slug>/', views.public_profile, name='public_profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bluetooth-sync/', views.bluetooth_sync, name='bluetooth_sync'),
    path('api/sync-to-badge/', views.sync_to_badge, name='sync_to_badge'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('contact/', views.contact, name='contact'),
]