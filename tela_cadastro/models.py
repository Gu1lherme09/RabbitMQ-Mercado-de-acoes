from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    chat_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.username
    

# ==========================================================
# 1︝⃣  AÇÃO (dados principais do ativo)
# ==========================================================
class Acao(models.Model):
    abreviacao = models.CharField(max_length=10, unique=True)  # Ex: PETR4
    nome = models.CharField(max_length=100)  # Ex: Petrobras PN
    nome_completo = models.CharField(max_length=200, blank=True, null=True)
    moeda = models.CharField(max_length=10, default="BRL")

    valor_atual = models.FloatField(default=0)
    alta_dia = models.FloatField(default=0)
    baixa_dia = models.FloatField(default=0)
    percentual_mudanca = models.FloatField(default=0)
    variacao = models.FloatField(default=0)
    volume = models.FloatField(default=0)
    preco_abertura = models.FloatField(default=0)
    preco_anterior = models.FloatField(default=0)
    faixa_dia = models.CharField(max_length=50, blank=True, null=True)
    market_cap = models.FloatField(default=0)

    logo_url = models.URLField(blank=True, null=True)
    setor = models.CharField(max_length=100, blank=True, null=True)
    industria = models.CharField(max_length=100, blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ação"
        verbose_name_plural = "Ações"
        ordering = ["abreviacao"]
        indexes = [
            models.Index(fields=["abreviacao"]),
        ]

    def __str__(self):
        return f"{self.abreviacao} - {self.nome}"


# ==========================================================
# 2︝⃣  HISTÓRICO DE PREÇOS (dados diários, semanais, etc.)
# ==========================================================
class AcaoHistorico(models.Model):
    class PeriodoChoices(models.TextChoices):
        D1 = "1d", "1 Dia"
        D5 = "5d", "5 Dias"
        M1 = "1mo", "1 Mês"
        M3 = "3mo", "3 Meses"
        M6 = "6mo", "6 Meses"
        Y1 = "1y", "1 Ano"
        Y2 = "2y", "2 Anos"
        Y5 = "5y", "5 Anos"
        Y10 = "10y", "10 Anos"
        YTD = "ytd", "Ano Corrente"
        MAX = "max", "Máximo"

    acao = models.ForeignKey(Acao, on_delete=models.CASCADE, related_name="historicos")
    data = models.DateField()
    abertura = models.FloatField(default=0)
    fechamento = models.FloatField(default=0)
    alta = models.FloatField(default=0)
    baixa = models.FloatField(default=0)
    volume = models.FloatField(default=0)
    variacao = models.FloatField(blank=True, null=True)
    periodo = models.CharField(
        max_length=10,
        choices=PeriodoChoices.choices,
        default=PeriodoChoices.D1,
        help_text="Intervalo dos dados históricos conforme BRAPI"
    )

    class Meta:
        verbose_name = "Histórico da Ação"
        verbose_name_plural = "Históricos das Ações"
        ordering = ["-data"]
        unique_together = ("acao", "data", "periodo")
        indexes = [
            models.Index(fields=["acao", "data"]),
        ]

    def __str__(self):
        return f"{self.acao.abreviacao} ({self.data}) - {self.periodo}"

    class Meta:
        verbose_name = "Perfil da Empresa"
        verbose_name_plural = "Perfis das Empresas"

    def __str__(self):
        return f"Perfil de {self.acao.abreviacao}"

class Monitoramento(models.Model):
    DIRECAO_CHOICES = [
        ('acima', 'Acima'),
        ('acima_ou_igual', 'Acima ou Igual'),
        ('abaixo', 'Abaixo'),
        ('abaixo_ou_igual', 'Abaixo ou Igual'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE)
    ativo = models.BooleanField(default=True)
    adicionado_em = models.DateTimeField(auto_now_add=True)
    preco_alvo = models.FloatField()
    direcao = models.CharField(max_length=20, choices=DIRECAO_CHOICES)
    
class Alerta(models.Model):
    TIPO_CHOICES =[
        ('preco', 'Preço'), 
        ('percentual', 'Percentual'), 
        ('volume', 'Volume'),
        ('market_cap', 'Market Cap'),
    ]
    
    OPERADO_CHOICES = [
        ('>', 'Maior que'),
        ('>=', 'Maior ou Igual a'),
        ('<', 'Menor que'),
        ('<=', 'Menor ou Igual a'),
        ('=', 'Igual a'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE)
    tipo_alerta = models.CharField(max_length=20, choices=TIPO_CHOICES)
    valor_referencia = models.FloatField()
    ativo = models.BooleanField(default=True)
    disparado = models.BooleanField(default=False)
    disparado_em = models.DateTimeField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Alerta"
        verbose_name_plural = "Alertas"
        indexes = [
            models.Index(fields=["usuario", "acao"]),
            models.Index(fields=["ativo", "disparado"])
        ]
        
    def __str__(self):
        return f"{self.usuario.email} - {self.acao.abreviacao} {self.operador} {self.valor_referencia}"
    
    
class NotificacaoUsuario(models.Model):
    TIPO_CHOICES =[
        ('alerta', 'Alerta'), 
        ('sistema', 'Sistema'), 
        ('dividendo', 'Dividendo'),
        ('informativo', 'Informativo'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    alerta = models.ForeignKey(Alerta, on_delete=models.SET_NULL, null=True, blank=True)
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    lida = models.BooleanField(default=False)
    enviada_telegram = models.BooleanField(default=False)  
    criado_em = models.DateTimeField(auto_now_add=True)    
    
    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["usuario", "lida"]),
            models.Index(fields=["enviada_telegram"]),
        ]
        
    def __str__(self):
        return f"{self.usuario.email} - {self.titulo}"
        
        
        
    