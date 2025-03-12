from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, logout
from .middlewares import guest, auth
from .models import ResetPassword
from django.urls import reverse
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm

# Create your views here.

# https://www.youtube.com/watch?v=_9K0MTBOKNs

@guest
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) 
            return redirect('dashboard')
    else:
        initial_data = {'username':'', 'email': '', 'password1':'','password2':""}
        form = CustomUserCreationForm(initial=initial_data)
    return render(request, 'auth/register.html', {'form': form}) 

@guest
def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        initial_data = {'username':'', 'password':''}
        form = CustomAuthenticationForm(initial=initial_data)
    return render(request, 'auth/login.html',{'form':form}) 

@auth
def dashboard_view(request):
    return render(request, 'dashboard.html')

@auth
def logout_view(request):
    logout(request)
    return redirect('login')
    
def forgot_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email=email)
                new_reset_obj = ResetPassword.objects.create(user=user)
                new_reset_obj.save()

                password_reset_url = reverse('reset-password', kwargs={'reset_id': new_reset_obj.token})
                full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'

                email_body = f'Reset your password using the link below:\n\n\n{full_password_reset_url}'
            
                email_message = EmailMessage(
                    'Reset your password', # email subject
                    email_body,
                    settings.EMAIL_HOST_USER, # email sender
                    [email] # email  receiver 
                )

                email_message.fail_silently = True
                email_message.send()

                return redirect('password-reset-sent', reset_id=new_reset_obj.token)

            except User.DoesNotExist:
                messages.error(request, f"No user with email '{email}' found")
                return redirect('forgot-password')
        else:
            print("Form is not valid")
            print(form.errors)
    else:
        form = CustomPasswordResetForm(initial={'email': ''})
    return render(request, 'auth/forgot_password.html', {'form': form})

def password_reset_sent_view(request, reset_id):

    if ResetPassword.objects.filter(token=reset_id).exists():
        return render(request, 'auth/password_reset_sent.html')
    else:
        # redirect to forgot password page if code does not exist
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')
    
def password_reset_view(request, reset_id):

    try:
        password_reset_id = ResetPassword.objects.get(token=reset_id)

        if request.method == "POST":
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            passwords_have_error = False

            if password != confirm_password:
                passwords_have_error = True
                messages.error(request, 'Passwords do not match')

            if len(password) < 5:
                passwords_have_error = True
                messages.error(request, 'Password must be at least 5 characters long')

            expiration_time = password_reset_id.created_at + timezone.timedelta(minutes=10)

            if timezone.now() > expiration_time:
                passwords_have_error = True
                messages.error(request, 'Reset link has expired')

                password_reset_id.delete()

            if not passwords_have_error:
                user = password_reset_id.user
                user.set_password(password)
                user.save()

                password_reset_id.delete()

                messages.success(request, 'Password reset successful!. Proceed to login')
                return redirect('login')
            else:
                # redirect back to password reset page and display errors
                return redirect('reset-password', reset_id=reset_id)

    except ResetPassword.DoesNotExist:
        # redirect to forgot password page if code does not exist
        messages.error(request, 'Invalid reset id')
        return redirect('forgot-password')

    return render(request, 'auth/reset_password.html')
    