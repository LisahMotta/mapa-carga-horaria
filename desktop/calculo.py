"""
Lógica de cálculo do Mapa de Carga Horária — Cálculo de Proventos (Aposentadoria).
ANEXO III — SEDUC / DIPES / CEVIF · Base: LC 836/97 (Art. 39 das DDTT).

Este módulo NÃO depende de interface gráfica, para permitir testes automatizados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

# Jornadas do PEB (horas mensais) -> nome
JORNADAS: Dict[int, str] = {
    96: "Jornada Reduzida",
    120: "Jornada Inicial",
    150: "Jornada Básica",
    200: "Jornada Completa",
}

# Períodos de opção previstos no manual (nº de meses -> descrição)
PERIODOS: Dict[int, str] = {
    60: "60 meses (últimos 60 meses)",
    84: "84 meses ininterruptos",
    120: "120 meses intercalados",
}


def chave(ano: int, mes: int) -> str:
    """Chave 'AAAA-MM' para um ano e mês (0-based)."""
    return f"{ano}-{mes + 1:02d}"


def periodo_meses(mes_final_ano: int, mes_final_mes: int, n_meses: int) -> List[Tuple[int, int]]:
    """
    Lista de (ano, mes 0-based) dos `n_meses` que terminam em (mes_final_ano, mes_final_mes),
    ordenada do mais antigo para o mais recente.
    """
    out: List[Tuple[int, int]] = []
    y, m = mes_final_ano, mes_final_mes
    for _ in range(n_meses):
        out.append((y, m))
        m -= 1
        if m < 0:
            m = 11
            y -= 1
    out.reverse()
    return out


@dataclass
class Resultado:
    total: int                 # 7.A — total geral da carga horária
    n_meses: int               # nº de meses da opção (campo 9)
    media: int                 # campo 10 — média arredondada ao inteiro
    jornada: int               # jornada atual (campo 6)
    tipo_quadro: str           # 'completo' ou 'unico'
    suplementar: int = 0       # carga suplementar (apenas no quadro completo)
    totais_anuais: Dict[int, int] = field(default_factory=dict)


def calcular(
    ch: Dict[str, float],
    vinculo: str,
    jornada: int,
    n_meses: int,
    mes_final_ano: int,
    mes_final_mes: int,
) -> Resultado:
    """
    Calcula o Mapa de Carga Horária.

    ch          -> {'AAAA-MM': horas}
    vinculo     -> 'titular' ou 'ofa'
    jornada     -> horas da jornada atual (96/120/150/200)
    n_meses     -> período de opção (60/84/120)
    mes_final_* -> ano e mês (0-based) do último mês do período

    Regras do campo 10 (conforme manual):
      - Titular de Cargo: preenche os 3 campos (Média = Jornada + Carga Suplementar).
        Se a Média for MENOR que a Jornada atual, preenche apenas o 1º quadro (Média).
      - OFA: preenche somente o 1º quadro (Média).
    """
    meses = periodo_meses(mes_final_ano, mes_final_mes, n_meses)
    ativos = {chave(a, m) for a, m in meses}

    total = 0
    for k in ativos:
        total += int(round(float(ch.get(k, 0) or 0)))

    media = round(total / n_meses) if n_meses > 0 else 0
    jornada = int(jornada)

    # totais por ano (apenas meses ativos)
    totais_anuais: Dict[int, int] = {}
    for a, m in meses:
        v = int(round(float(ch.get(chave(a, m), 0) or 0)))
        totais_anuais[a] = totais_anuais.get(a, 0) + v

    if vinculo == "ofa" or media < jornada:
        return Resultado(
            total=total, n_meses=n_meses, media=media, jornada=jornada,
            tipo_quadro="unico", suplementar=0, totais_anuais=totais_anuais,
        )

    return Resultado(
        total=total, n_meses=n_meses, media=media, jornada=jornada,
        tipo_quadro="completo", suplementar=media - jornada, totais_anuais=totais_anuais,
    )


def anos_do_periodo(meses: List[Tuple[int, int]]) -> List[int]:
    return sorted({a for a, _ in meses})
