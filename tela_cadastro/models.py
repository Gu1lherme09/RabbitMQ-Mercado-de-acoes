from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
    

# ==========================================================
# 1️⃣  AÇÃO (dados principais do ativo)
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
# 2️⃣  HISTÓRICO DE PREÇOS (dados diários, semanais, etc.)
# ==========================================================
class AcaoHistorico(models.Model):
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE, related_name="historicos")
    data = models.DateField()
    abertura = models.FloatField(default=0)
    fechamento = models.FloatField(default=0)
    alta = models.FloatField(default=0)
    baixa = models.FloatField(default=0)
    volume = models.FloatField(default=0)
    variacao = models.FloatField(blank=True, null=True)
    periodo = models.CharField(max_length=10, default="1d")  # Ex: "1d", "5d"

    class Meta:
        verbose_name = "Histórico da Ação"
        verbose_name_plural = "Históricos das Ações"
        ordering = ["-data"]
        unique_together = ("acao", "data", "periodo")
        indexes = [
            models.Index(fields=["acao", "data"]),
        ]

    def __str__(self):
        return f"{self.acao.abreviacao} ({self.data})"


# ==========================================================
# 3️⃣  DIVIDENDOS (pagamentos e eventos financeiros)
# ==========================================================
class Dividendo(models.Model):
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE, related_name="dividendos")
    tipo = models.CharField(max_length=100, blank=True, null=True)
    data_pagamento = models.DateField(blank=True, null=True)
    valor = models.FloatField(default=0)
    descricao = models.TextField(blank=True, null=True)
    ultima_data_prior = models.DateField(blank=True, null=True)
    aprovado_em = models.DateField(blank=True, null=True)
    isin_code = models.CharField(max_length=50, blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Dividendo"
        verbose_name_plural = "Dividendos"
        ordering = ["-data_pagamento"]
        indexes = [
            models.Index(fields=["acao", "data_pagamento"]),
        ]

    def __str__(self):
        return f"{self.acao.abreviacao} - {self.tipo or 'Dividendo'}"


# ==========================================================
# 4️⃣  PERFIL DA EMPRESA (dados estáticos e institucionais)
# ==========================================================
class EmpresaPerfil(models.Model):
    acao = models.OneToOneField(Acao, on_delete=models.CASCADE, related_name="perfil")
    endereco = models.CharField(max_length=200, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    setor = models.CharField(max_length=100, blank=True, null=True)
    industria = models.CharField(max_length=100, blank=True, null=True)
    funcionarios = models.IntegerField(blank=True, null=True)
    descricao_longa = models.TextField(blank=True, null=True)
    site = models.URLField(blank=True, null=True)
    telefone = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "Perfil da Empresa"
        verbose_name_plural = "Perfis das Empresas"

    def __str__(self):
        return f"Perfil de {self.acao.abreviacao}"