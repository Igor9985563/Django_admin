from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import CombinedRegisterForm  # обновлённая форма с avatar и bio
from .models import Profile


def register(request):
    if request.method == 'POST':
        form = CombinedRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Профиль уже создан сигналом — только обновим данные
            profile = user.profile
            profile.bio = form.cleaned_data.get('bio')
            profile.avatar = form.cleaned_data.get('avatar')
            profile.save()
            messages.success(request, f'Аккаунт создан для {user.username}! Теперь вы можете войти.')
            return redirect('login')
    else:
        form = CombinedRegisterForm()
    return render(request, 'registration/register.html', {'form': form})
