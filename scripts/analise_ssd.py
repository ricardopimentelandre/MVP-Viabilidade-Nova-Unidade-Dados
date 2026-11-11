"""Análises P1–P4 do SSD de viabilidade de nova unidade de infraestrutura de dados.

Reproduz, sem alterações, a metodologia do notebook original (MVP_Viabilidade_Nova_Unidade_Dados.ipynb):
- percentil empírico = fração de projetos históricos com valor <= v, vezes 100;
- índice geral = média simples (pesos iguais) dos percentis de custo, risco e prazo;
- faixas heurísticas: Favorável (< 33), Atenção (33 a < 67), Crítica (>= 67);
- recomendação por dimensão quando o percentil da dimensão é >= 67.

Pesos, cortes e limiares são HIPÓTESES DE PROJETO (não validados por especialistas) e o índice
mede exposição RELATIVA à base histórica: não é probabilidade de inviabilidade, nem previsão.
Nenhum modelo de aprendizado de máquina é usado.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.pipeline_etl_drive import ler_csv, preparar_prata, sha256_arquivo

DIMENSOES: dict[str, dict[str, str]] = {
    "custo": {"coluna": "Estimated_Cost_USD", "rotulo": "Custo estimado (US$)"},
    "risco": {"coluna": "Risk_Assessment_Score", "rotulo": "Escore de risco (0–100)"},
    "prazo": {"coluna": "Time_Estimate_Days", "rotulo": "Prazo estimado (dias)"},
}

# Heurísticas do MVP original (não alterar sem autorização).
CORTE_FAVORAVEL = 33
CORTE_CRITICA = 67
LIMIAR_RECOMENDACAO = 67
LIMITE_RISCO = 100  # o escore de risco é tratado como escala 0–100

FAIXA_FAVORAVEL, FAIXA_ATENCAO, FAIXA_CRITICA = "FAVORÁVEL", "ATENÇÃO", "CRÍTICA"


def carregar_prata(pasta_execucao: Path | str) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Lê a prata gravada em uma execução do pipeline e confere SHA-256 e contagens do manifesto.

    Não grava nada na pasta de execução. Levanta AssertionError se a prata lida divergir.
    """
    pasta = Path(pasta_execucao)
    manifesto = json.loads((pasta / "evidencias" / "manifesto_execucao.json").read_text(encoding="utf-8"))
    caminho = pasta / "prata" / "projetos_infraestrutura_flat.csv"
    if not caminho.is_file():
        raise AssertionError(f"Prata não encontrada: {caminho}")
    if sha256_arquivo(caminho) != manifesto["sha256_prata"]:
        raise AssertionError("SHA-256 da prata lida difere do manifesto.")
    prata = preparar_prata(ler_csv(caminho))
    if len(prata) != manifesto["registros_prata"]:
        raise AssertionError("Número de registros da prata difere do manifesto.")
    return prata, manifesto


def percentil_empirico(valor: float, serie: pd.Series) -> float:
    """Mesma regra do notebook original: (serie <= valor).mean() * 100."""
    return float((serie <= valor).mean() * 100)


def classificar(indice: float) -> str:
    if indice < CORTE_FAVORAVEL:
        return FAIXA_FAVORAVEL
    if indice < CORTE_CRITICA:
        return FAIXA_ATENCAO
    return FAIXA_CRITICA


# ---------------------------------------------------------------- P1
def estatisticas_descritivas(df: pd.DataFrame) -> pd.DataFrame:
    """P1: estatísticas descritivas das três dimensões (mín, quartis, máx, média, dispersão)."""
    linhas = {}
    for nome, d in DIMENSOES.items():
        s = df[d["coluna"]].astype(float)
        q1, mediana, q3 = s.quantile([0.25, 0.5, 0.75])
        iqr = q3 - q1
        fora = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
        linhas[nome] = {
            "n": int(s.count()), "minimo": s.min(), "q1": q1, "mediana": mediana, "q3": q3,
            "maximo": s.max(), "media": s.mean(), "desvio_padrao": s.std(),
            "coef_variacao_%": s.std() / s.mean() * 100, "assimetria": s.skew(),
            "iqr": iqr, "outliers_iqr": fora,
        }
    return pd.DataFrame(linhas).T


def correlacoes(df: pd.DataFrame) -> pd.DataFrame:
    """Correlação de Pearson entre as três dimensões (P1: elas variam juntas?)."""
    cols = {nome: d["coluna"] for nome, d in DIMENSOES.items()}
    return df[list(cols.values())].rename(columns={v: k for k, v in cols.items()}).corr()


def resumo_por_rotulo(df: pd.DataFrame) -> pd.DataFrame:
    """Médias das três dimensões por Feasibility_Label (rótulo da fonte, não verdade de campo)."""
    cols = [d["coluna"] for d in DIMENSOES.values()]
    r = df.groupby("Feasibility_Label")[cols].mean()
    r.insert(0, "n", df["Feasibility_Label"].value_counts())
    return r


# ---------------------------------------------------------------- P2 / P3
def recomendacoes(percentis: dict[str, float], faixa: str) -> list[str]:
    """Textos idênticos aos do notebook original."""
    rec = []
    rec.append(
        "Revisar orçamento, fornecedores e criar reserva de contingência."
        if percentis["custo"] >= LIMIAR_RECOMENDACAO
        else "Custo dentro de uma faixa administrável frente aos projetos históricos."
    )
    rec.append(
        "Elaborar plano formal de mitigação de riscos antes da implantação."
        if percentis["risco"] >= LIMIAR_RECOMENDACAO
        else "Manter monitoramento periódico dos riscos do projeto."
    )
    rec.append(
        "Dividir a implantação em etapas e acompanhar marcos críticos do cronograma."
        if percentis["prazo"] >= LIMIAR_RECOMENDACAO
        else "Prazo está em faixa administrável frente aos projetos históricos."
    )
    if faixa == FAIXA_FAVORAVEL:
        rec.append("O projeto apresenta condições favoráveis para avançar ao planejamento detalhado.")
    elif faixa == FAIXA_ATENCAO:
        rec.append("Recomenda-se revisar os principais pontos de atenção antes da aprovação definitiva.")
    else:
        rec.append("Recomenda-se não iniciar a implantação sem revisão do planejamento.")
    return rec


def avaliar_cenario(df: pd.DataFrame, custo: float, risco: float, prazo: float) -> dict[str, Any]:
    """P2 (percentis) e P3 (índice, faixa, recomendações) de um cenário."""
    valores = {"custo": custo, "risco": risco, "prazo": prazo}
    percentis = {n: percentil_empirico(valores[n], df[DIMENSOES[n]["coluna"]]) for n in DIMENSOES}
    indice = sum(percentis.values()) / 3  # pesos iguais
    faixa = classificar(indice)
    return {
        "valores": valores, "percentis": percentis, "indice": indice, "faixa": faixa,
        "contribuicao_%": {n: percentis[n] / sum(percentis.values()) * 100 if sum(percentis.values()) else 0.0
                           for n in DIMENSOES},
        "recomendacoes": recomendacoes(percentis, faixa),
    }


def comparar_cenarios(df: pd.DataFrame, cenarios: dict[str, tuple[float, float, float]]) -> pd.DataFrame:
    """P4: tabela comparativa de cenários nomeados (custo, risco, prazo)."""
    linhas = []
    for nome, (c, r, p) in cenarios.items():
        a = avaliar_cenario(df, c, r, p)
        linhas.append({
            "cenario": nome, "custo_usd": c, "risco": r, "prazo_dias": p,
            "pct_custo": a["percentis"]["custo"], "pct_risco": a["percentis"]["risco"],
            "pct_prazo": a["percentis"]["prazo"], "indice": a["indice"], "faixa": a["faixa"],
            "n_alertas": sum(a["percentis"][n] >= LIMIAR_RECOMENDACAO for n in DIMENSOES),
        })
    return pd.DataFrame(linhas).set_index("cenario")


# ---------------------------------------------------------------- P4
def _variar(base: dict[str, float], dimensao: str, valor: float) -> dict[str, float]:
    novo = dict(base)
    novo[dimensao] = valor
    return novo


def sensibilidade_uma_dimensao(
    df: pd.DataFrame, base: dict[str, float], variacoes_pct: list[float],
) -> pd.DataFrame:
    """P4: varia UMA dimensão por vez (as outras ficam no cenário-base), em % do valor-base.

    O risco é limitado a 100 (teto da escala assumida). O custo e o prazo não têm teto.
    """
    linhas = []
    for dim in DIMENSOES:
        for v in variacoes_pct:
            valor = base[dim] * (1 + v / 100)
            if dim == "risco":
                valor = min(valor, LIMITE_RISCO)
            novo = _variar(base, dim, valor)
            a = avaliar_cenario(df, novo["custo"], novo["risco"], novo["prazo"])
            linhas.append({
                "dimensao": dim, "variacao_%": v, "valor": valor,
                "percentil_da_dimensao": a["percentis"][dim], "indice": a["indice"], "faixa": a["faixa"],
            })
    return pd.DataFrame(linhas)


def curva_indice(df: pd.DataFrame, base: dict[str, float], dimensao: str, pontos: int = 80) -> pd.DataFrame:
    """P4: índice ao varrer uma dimensão por toda a faixa observada, com as outras fixas."""
    s = df[DIMENSOES[dimensao]["coluna"]].astype(float)
    lo, hi = float(s.min()), float(s.max())
    linhas = []
    for i in range(pontos):
        valor = lo + (hi - lo) * i / (pontos - 1)
        novo = _variar(base, dimensao, valor)
        a = avaliar_cenario(df, novo["custo"], novo["risco"], novo["prazo"])
        linhas.append({"valor": valor, "indice": a["indice"]})
    return pd.DataFrame(linhas)


def ponto_de_virada(
    df: pd.DataFrame, base: dict[str, float], dimensao: str, corte: float = CORTE_CRITICA,
) -> dict[str, Any]:
    """P4: maior valor da dimensão que mantém o índice ABAIXO do corte (outras dimensões fixas).

    O percentil só muda nos valores observados, então basta varrer os valores distintos da base.
    Retorna None em 'valor' se nem o menor valor observado deixa o índice abaixo do corte.
    """
    s = df[DIMENSOES[dimensao]["coluna"]].astype(float)
    candidatos = sorted(s.unique())
    abaixo = []
    for valor in candidatos:
        novo = _variar(base, dimensao, valor)
        if avaliar_cenario(df, novo["custo"], novo["risco"], novo["prazo"])["indice"] < corte:
            abaixo.append(valor)
    if not abaixo:
        return {"dimensao": dimensao, "corte": corte, "valor": None, "variacao_%": None, "alcancavel": False}
    valor = float(max(abaixo))
    return {
        "dimensao": dimensao, "corte": corte, "valor": valor,
        "variacao_%": float((valor / base[dimensao] - 1) * 100), "alcancavel": True,
    }


def sensibilidade_em_desvios(
    df: pd.DataFrame, base: dict[str, float], desvios: list[float],
) -> pd.DataFrame:
    """P4: varia UMA dimensão por vez em múltiplos do desvio-padrão histórico da própria dimensão.

    Complementa a variação percentual: como cada dimensão tem dispersão diferente, o mesmo
    percentual equivale a "saltos" diferentes. Em desvios, as dimensões ficam comparáveis.
    """
    linhas = []
    for dim in DIMENSOES:
        dp = float(df[DIMENSOES[dim]["coluna"]].astype(float).std())
        for k in desvios:
            valor = base[dim] + k * dp
            if dim == "risco":
                valor = min(valor, LIMITE_RISCO)
            novo = _variar(base, dim, valor)
            a = avaliar_cenario(df, novo["custo"], novo["risco"], novo["prazo"])
            linhas.append({
                "dimensao": dim, "desvios": k, "valor": valor,
                "percentil_da_dimensao": a["percentis"][dim], "indice": a["indice"], "faixa": a["faixa"],
            })
    return pd.DataFrame(linhas)


def indice_historico(df: pd.DataFrame) -> pd.DataFrame:
    """P3: aplica o mesmo índice a cada projeto histórico (percentil de cada dimensão na própria base).

    Serve para ver como a heurística distribui os projetos nas faixas e se o índice se relaciona
    com o Feasibility_Label da fonte. NÃO é uma validação do índice nem do rótulo.
    """
    n = len(df)
    pct = {
        nome: df[d["coluna"]].astype(float).rank(method="max") / n * 100  # == (serie <= v).mean() * 100
        for nome, d in DIMENSOES.items()
    }
    out = pd.DataFrame(pct)
    out["indice"] = out[list(DIMENSOES)].mean(axis=1)
    out["faixa"] = out["indice"].map(classificar)
    out["Feasibility_Label"] = df["Feasibility_Label"].values
    return out
