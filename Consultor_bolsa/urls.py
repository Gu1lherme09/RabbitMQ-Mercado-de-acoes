"""
URL configuration for Consultor_bolsa project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static

from Consultor_bolsa import settings
from api.views import atualizar_acoes_completas
from . import view
from tela_cadastro import views as tc

urlpatterns = [
    path('admin/', admin.site.urls),

    # ------------------------- Home -------------------------------
    path('home/', view.home, name='home'),
    # --------------------------------------------------------------

    # ------------------------- Consulta ---------------------------
    path('consultar/', view.consultar_acoes, name="consultar"),
    # --------------------------------------------------------------

    # ------------------------- Tela de cadastro -------------------
    path('registro/', tc.registro_view, name='registro'),
    path('', tc.login_view, name='login'),
    path('logout/', tc.logout_view, name='logout'),
    # --------------------------------------------------------------

    # ------------------------- teste -------------------
    path('api/testar-essencial/', atualizar_acoes_completas, name='testar_essencial'),
    # --------------------------------------------------------------
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
