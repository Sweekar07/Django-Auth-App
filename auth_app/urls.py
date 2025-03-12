from django.urls import path

from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('forgot-password/', views.forgot_password_view, name='forgot-password'),
    path('password-reset-sent/<str:reset_id>/', views.password_reset_sent_view, name='password-reset-sent'),
    path('reset-password/<str:reset_id>/', views.password_reset_view, name='reset-password'),
]