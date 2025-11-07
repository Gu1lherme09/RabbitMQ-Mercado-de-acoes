from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from tela_cadastro.models import Acao

@login_required(login_url='login')
def home(request):
    return render(request, 'home/home.html')

@login_required(login_url='login')
def consultar_acoes(request):
    acoes = Acao.objects.all()
    return render(request,'consultar/consultar.html',{'acoes': acoes})