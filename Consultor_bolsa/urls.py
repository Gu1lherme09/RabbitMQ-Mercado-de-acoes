from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static

from consultor_bolsa import settings
from api import views as brapi
from . import view
from tela_cadastro import views as tc

urlpatterns = [
    path('admin/', admin.site.urls),

    # ------------------------- Home -------------------------------
    path('home/', view.home, name='home'),
    # --------------------------------------------------------------

    # ------------------------- Consulta ---------------------------
    path('consultar/', view.consultar_acoes, name="consultar"),
    path('monitoramento/criar/', view.criar_monitoramento, name='criar_monitoramento'),
    # --------------------------------------------------------------

    # ------------------------- Tela de cadastro -------------------
    path('registro/', tc.registro_view, name='registro'),
    path('', tc.login_view, name='login'),
    path('logout/', tc.logout_view, name='logout'),
    # --------------------------------------------------------------

    # ------------------------- brapi ------------------------------
    path("ajax/adicionar-acao-completa/", brapi.adicionar_acao_completa, name="ajax_adicionar_acao_completa"),
    path('api/testar-essencial/', brapi.atualizar_acoes_completas, name='testar_essencial'),
    path("api/historico/<str:ticker>/", brapi.historico_acao, name="ajax_historico_acao"),
    # --------------------------------------------------------------

    # ------------------------- Gráfico ----------------------------
    path("banco/acoes/basicas/", view.dados_basicos_acoes, name="api_dados_basicos_acoes"),
    path("banco/historico_ou_basico/<str:ticker>/", view.historico_ou_basico, name="api_historico_ou_basico"),
    # --------------------------------------------------------------
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
