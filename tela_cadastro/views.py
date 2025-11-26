from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages

from tela_cadastro.models import Acao, Monitoramento
from .forms import LoginForm, RegistroForm

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)  # 👈 sem passar request
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'cadastro/login.html', {'form': form})


def registro_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistroForm()
    return render(request, 'cadastro/registro.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')

def perfil_view(request):
    """Tela de configuração do perfil do usuário"""
    if request.method == 'POST':
        chat_id = request.POST.get('chat_id', '').strip()
        
        if chat_id:
            request.user.chat_id = chat_id
            request.user.save()
            messages.success(request, 'Chat ID configurado com sucesso! Você receberá alertas no Telegram.')
        else:
            messages.error(request, 'Por favor, informe um Chat ID válido.')
        
        return redirect('perfil')
    
    return render(request, 'perfil/perfil.html')
