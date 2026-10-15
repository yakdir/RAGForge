"""Accounts views."""
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render


def login_page(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'accounts/login.html', {'error': '邮箱或密码错误'})
    return render(request, 'accounts/login.html')


def logout_page(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('/accounts/login/')


def profile(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    return render(request, 'accounts/profile.html', {
        'user': request.user,
    })


def change_password(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/')
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})
