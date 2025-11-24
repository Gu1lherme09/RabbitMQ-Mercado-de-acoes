import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)
    chat_id = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.username
    

class Acao(models.Model):
    abreviacao = models.CharField(max_length=10, unique=True)  
    nome = models.CharField(max_length=100)  
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


class Worker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hostname = models.CharField(max_length=100)
    pid = models.IntegerField()
    is_leader = models.BooleanField(default=False)
    uptime_segundos = models.BigIntegerField(default=0)
    last_heartbeat = models.DateTimeField(auto_now=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hostname} ({self.pid})"