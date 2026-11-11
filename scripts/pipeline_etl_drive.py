"""ETL auditável: Kaggle -> Colab/Pandas -> Google Drive (bronze e prata).

A execução real no Drive deve ser feita pelo notebook Colab. Este módulo também
expõe processar_csv() e verificar_persistencia() para testes locais sem Kaggle,
autenticação ou rede. Os dados não são publicados no GitHub.

Regras centrais:
- a bronze é a cópia byte a byte do CSV de origem;
- a prata mantém os 13 atributos, a ordem e todos os registros (tipagem apenas);
- a auditoria só diagnostica; nunca remove, corrige ou imputa registros.
"""
from __future__ import annotations

import hashlib
import json
import platform
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DATASET_HANDLE = "ziya07/engineering-project-cost-feasibility-dataset"
DATASET_URL = "https://www.kaggle.com/datasets/ziya07/engineering-project-cost-feasibility-dataset"
VERSAO_KAGGLE = 1

# Metadados transcritos da API pública do Kaggle (não vêm do arquivo baixado).
# A licença deve ser reconferida na página do dataset antes da entrega.
FONTE_METADADOS: dict[str, Any] = {
    "licenca": "CC0: Public Domain",
    "versao": VERSAO_KAGGLE,
    "ultima_atualizacao_utc": "2025-07-28T12:56:33Z",
    "tamanho_total_bytes": 261932,
    "consultado_em": "2026-11-11",
    "consultado_via": "https://www.kaggle.com/api/v1/datasets/view/" + DATASET_HANDLE,
    "nota": "Valores transcritos da API do Kaggle; confirmar a licença na página do dataset.",
}
# SHA-256 do CSV da versão 1, calculado em download independente em 2026-11-11.
SHA256_CSV_V1 = "a93b9f10f889c95145dc5bdae9894a42582bb04c51b3bd1817ef515ff5920dc6"

COLUNAS_ESPERADAS = [
    "Project_ID",
    "Project_Name",
    "Project_Type",
    "Scope_Complexity",
    "Estimated_Cost_USD",
    "Resource_Allocation_Score",
    "Risk_Assessment_Score",
    "Environmental_Impact_Score",
    "Historical_Cost_Deviation_%",
    "Stakeholder_Priority_Score",
    "Time_Estimate_Days",
    "Feasibility_Label",
    "Scope_Complexity_Numeric",
]

COLUNAS_TEXTO = [
    "Project_ID", "Project_Name", "Project_Type",
    "Scope_Complexity", "Feasibility_Label",
]
COLUNAS_NUMERICAS = [c for c in COLUNAS_ESPERADAS if c not in COLUNAS_TEXTO]

MAPEAMENTO_COMPLEXIDADE = {"Low": 1, "Medium": 2, "High": 3}

# Domínios dos atributos. Dois níveis, que não devem ser confundidos:
#  - "esperado_*"/"categorias"/"padrao": regra de VALIDAÇÃO. Violação é sinalizada.
#  - "observado_v1": o que a versão 1 do dataset realmente contém. Fora disso é
#    apenas informativo (a fonte não documenta domínios numéricos).
# "origem_dominio" indica de onde vem a regra: documentado_na_fonte (descrição do
# Kaggle), observado_v1 (inferido dos dados) ou convencao_do_projeto (hipótese nossa).
DOMINIOS: dict[str, dict[str, Any]] = {
    "Project_ID": {
        "tipo": "texto (identificador)",
        "padrao": r"^P\d{4}$",
        "origem_dominio": "observado_v1",
        "observado_v1": {"primeiro": "P0001", "ultimo": "P3245", "unicos": 3245},
        "justificativa": "Padrão P + 4 dígitos observado em todos os registros; assumido para novas cargas.",
    },
    "Project_Name": {
        "tipo": "categórico",
        "categorias": ["Dam Reinforcement", "Industrial Complex", "Highway Expansion",
                       "Smart Solar Grid", "Urban Flyover"],
        "origem_dominio": "observado_v1",
        "justificativa": "A fonte não lista as categorias; foram as 5 observadas na v1.",
    },
    "Project_Type": {
        "tipo": "categórico",
        "categorias": ["Road", "Power Plant", "Building", "Bridge", "Water Infra"],
        "origem_dominio": "observado_v1",
        "justificativa": "A fonte não lista as categorias; foram as 5 observadas na v1.",
    },
    "Scope_Complexity": {
        "tipo": "categórico ordinal",
        "categorias": ["Low", "Medium", "High"],
        "origem_dominio": "observado_v1",
        "justificativa": "3 níveis observados; concorda 1:1 com Scope_Complexity_Numeric.",
    },
    "Estimated_Cost_USD": {
        "tipo": "numérico (inteiro, USD)",
        "esperado_min": 0, "min_exclusivo": True, "esperado_max": None, "inteiro": True,
        "observado_v1": {"min": 1000404, "max": 6998223},
        "origem_dominio": "convencao_do_projeto",
        "justificativa": "Custo deve ser positivo; sem teto por não haver limite documentado.",
    },
    "Resource_Allocation_Score": {
        "tipo": "numérico (escore, inteiro)",
        "esperado_min": 0, "esperado_max": 100, "inteiro": True,
        "observado_v1": {"min": 50, "max": 99},
        "origem_dominio": "convencao_do_projeto",
        "justificativa": "Escala 0–100 assumida para escores; a fonte não documenta a escala.",
    },
    "Risk_Assessment_Score": {
        "tipo": "numérico (escore, inteiro)",
        "esperado_min": 0, "esperado_max": 100, "inteiro": True,
        "observado_v1": {"min": 30, "max": 99},
        "origem_dominio": "convencao_do_projeto",
        "justificativa": "Escala 0–100 assumida; premissa: valor maior = risco maior (não documentado).",
    },
    "Environmental_Impact_Score": {
        "tipo": "numérico (escore, inteiro)",
        "esperado_min": 0, "esperado_max": 100, "inteiro": True,
        "observado_v1": {"min": 20, "max": 99},
        "origem_dominio": "convencao_do_projeto",
        "justificativa": "Escala 0–100 assumida; a fonte não documenta a escala.",
    },
    "Historical_Cost_Deviation_%": {
        "tipo": "numérico (decimal, %)",
        "esperado_min": 0, "esperado_max": None, "inteiro": False,
        "observado_v1": {"min": 0.0, "max": 10.0},
        "origem_dominio": "convencao_do_projeto",
        "justificativa": "Tratado como magnitude não negativa (hipótese); v1 contém só 0–10, sem teto imposto.",
    },
    "Stakeholder_Priority_Score": {
        "tipo": "numérico (decimal, fração)",
        "esperado_min": 0.0, "esperado_max": 1.0, "inteiro": False,
        "observado_v1": {"min": 0.5, "max": 1.0},
        "origem_dominio": "observado_v1",
        "justificativa": (
            "Observado 0,50–1,00 (51 valores, passo 0,01), logo escala fracionária e NÃO 0–100. "
            "Valida-se em [0, 1], a faixa natural de uma fração, e não só em [0,5, 1,0]: o piso de "
            "0,5 pode ser característica desta amostra e não regra do negócio. Valores em [0, 0,5) "
            "são contados à parte como 'fora do observado' (informativo)."
        ),
    },
    "Time_Estimate_Days": {
        "tipo": "numérico (inteiro, dias)",
        "esperado_min": 0, "min_exclusivo": True, "esperado_max": None, "inteiro": True,
        "observado_v1": {"min": 120, "max": 599},
        "origem_dominio": "convencao_do_projeto",
        "justificativa": "Prazo deve ser positivo; sem teto por não haver limite documentado.",
    },
    "Feasibility_Label": {
        "tipo": "categórico (rótulo-alvo da fonte)",
        "categorias": ["Feasible", "Not Feasible", "Borderline"],
        "origem_dominio": "documentado_na_fonte",
        "justificativa": "Categorias citadas na descrição do Kaggle (Target Column). Rótulo da fonte, não verdade de campo.",
    },
    "Scope_Complexity_Numeric": {
        "tipo": "numérico (código ordinal)",
        "valores_validos": [1, 2, 3], "inteiro": True,
        "observado_v1": {"min": 1, "max": 3},
        "origem_dominio": "observado_v1",
        "justificativa": "Código 1/2/3 equivalente a Low/Medium/High (conferido sem exceções na v1).",
    },
}
assert set(DOMINIOS) == set(COLUNAS_ESPERADAS)


def sha256_arquivo(caminho: Path) -> str:
    digest = hashlib.sha256()
    with Path(caminho).open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def ler_csv(caminho: Path) -> pd.DataFrame:
    """Lê textos como strings, preservando zeros à esquerda em Project_ID."""
    return pd.read_csv(
        caminho,
        encoding="utf-8",
        dtype={col: "string" for col in COLUNAS_TEXTO},
    )


def validar_esquema(df: pd.DataFrame) -> None:
    faltantes = [col for col in COLUNAS_ESPERADAS if col not in df.columns]
    extras = [col for col in df.columns if col not in COLUNAS_ESPERADAS]
    if faltantes or extras:
        raise ValueError(f"Esquema diferente do esperado. Faltantes: {faltantes}; extras: {extras}")
    if len(df) == 0:
        raise ValueError("O conjunto de dados não possui registros.")


def preparar_prata(bronze: pd.DataFrame) -> pd.DataFrame:
    """Modelo flat: 13 atributos e mesma ordem de registros, sem exclusão de linhas."""
    validar_esquema(bronze)
    prata = bronze[COLUNAS_ESPERADAS].copy()
    for coluna in COLUNAS_TEXTO:
        prata[coluna] = prata[coluna].astype("string")
    for coluna in COLUNAS_NUMERICAS:
        try:
            prata[coluna] = pd.to_numeric(prata[coluna], errors="raise")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Coluna numérica inválida: {coluna}") from exc
    return prata


def _numero_ou_nulo(valor: Any) -> float | None:
    if pd.isna(valor) or not np.isfinite(float(valor)):
        return None
    return float(valor)


def _auditar_numerica(serie: pd.Series, dominio: dict[str, Any]) -> dict[str, Any]:
    n = pd.to_numeric(serie, errors="coerce")
    validos = n.dropna()
    dados: dict[str, Any] = {
        "tipo_pandas": str(serie.dtype),
        "nulos": int(serie.isna().sum()),
        "valores_unicos": int(serie.nunique(dropna=True)),
        "minimo_observado": _numero_ou_nulo(n.min()),
        "maximo_observado": _numero_ou_nulo(n.max()),
        "nao_finitos": int((~np.isfinite(validos)).sum()),
    }
    if "valores_validos" in dominio:
        fora = ~validos.isin(dominio["valores_validos"])
    else:
        fora = pd.Series(False, index=validos.index)
        if dominio.get("esperado_min") is not None:
            if dominio.get("min_exclusivo"):
                fora |= validos <= dominio["esperado_min"]
            else:
                fora |= validos < dominio["esperado_min"]
        if dominio.get("esperado_max") is not None:
            fora |= validos > dominio["esperado_max"]
    dados["fora_do_dominio_esperado"] = int(fora.sum())
    obs = dominio["observado_v1"]
    dados["fora_do_observado_v1"] = int(((validos < obs["min"]) | (validos > obs["max"])).sum())
    if dominio.get("inteiro"):
        dados["nao_inteiros"] = int((validos % 1 != 0).sum())
    if "valores_validos" not in dominio and len(validos) >= 4:
        q1, q3 = validos.quantile(0.25), validos.quantile(0.75)
        iqr = q3 - q1
        baixo, alto = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        dados["outliers_iqr"] = {
            "limite_inferior": _numero_ou_nulo(baixo),
            "limite_superior": _numero_ou_nulo(alto),
            "quantidade": int(((validos < baixo) | (validos > alto)).sum()),
        }
    return dados


def _auditar_texto(serie: pd.Series, coluna: str, dominio: dict[str, Any]) -> dict[str, Any]:
    texto = serie.astype("string")
    validos = texto.dropna()
    dados: dict[str, Any] = {
        "tipo_pandas": str(serie.dtype),
        "nulos": int(serie.isna().sum()),
        "valores_unicos": int(serie.nunique(dropna=True)),
        "vazios_ou_espacos": int(texto.fillna("").str.strip().eq("").sum()),
        "com_espacos_nas_bordas": int((validos != validos.str.strip()).sum()),
    }
    if "padrao" in dominio:
        dados["fora_do_dominio_esperado"] = int((~validos.str.match(dominio["padrao"])).sum())
    else:
        fora = validos[~validos.isin(dominio["categorias"])]
        dados["fora_do_dominio_esperado"] = int(len(fora))
        dados["valores_fora_do_dominio"] = sorted(map(str, fora.unique()))[:10]
        dados["categorias_mais_frequentes"] = {
            str(chave): int(valor)
            for chave, valor in texto.value_counts(dropna=False).head(12).items()
        }
    return dados


def auditar_prata(prata: pd.DataFrame) -> dict[str, Any]:
    """Auditoria diagnóstica por atributo. Não corrige nem remove registros."""
    validar_esquema(prata)
    atributos: dict[str, dict[str, Any]] = {}
    for coluna in COLUNAS_ESPERADAS:
        dominio = DOMINIOS[coluna]
        if coluna in COLUNAS_NUMERICAS:
            atributos[coluna] = _auditar_numerica(prata[coluna], dominio)
        else:
            atributos[coluna] = _auditar_texto(prata[coluna], coluna, dominio)

    pares = prata[["Scope_Complexity", "Scope_Complexity_Numeric"]].dropna()
    unicos = pares.drop_duplicates()
    categorias_com_multiplos_codigos = int(
        (unicos.groupby("Scope_Complexity")["Scope_Complexity_Numeric"].nunique() > 1).sum()
    )
    codigos_com_multiplas_categorias = int(
        (unicos.groupby("Scope_Complexity_Numeric")["Scope_Complexity"].nunique() > 1).sum()
    )
    esperado = pares["Scope_Complexity"].map(MAPEAMENTO_COMPLEXIDADE)
    fora_do_mapeamento = int((esperado != pares["Scope_Complexity_Numeric"]).sum())

    com_violacao = [c for c, d in atributos.items() if d["fora_do_dominio_esperado"] > 0]
    return {
        "linhas": int(len(prata)),
        "colunas": int(len(prata.columns)),
        "linhas_duplicadas_exatas": int(prata.duplicated(keep="first").sum()),
        "project_id_duplicados": int(prata["Project_ID"].duplicated(keep="first").sum()),
        "inconsistencias_categoria_para_codigo_complexidade": categorias_com_multiplos_codigos,
        "inconsistencias_codigo_para_categoria_complexidade": codigos_com_multiplas_categorias,
        "complexidade_fora_do_mapeamento_low_medium_high": fora_do_mapeamento,
        "resumo": {
            "atributos_com_violacao_do_dominio_esperado": com_violacao,
            "total_violacoes_dominio_esperado": int(
                sum(d["fora_do_dominio_esperado"] for d in atributos.values())
            ),
            "total_outliers_iqr_informativo": int(
                sum(d.get("outliers_iqr", {}).get("quantidade", 0) for d in atributos.values())
            ),
        },
        "atributos": atributos,
        "dominios_referencia": DOMINIOS,
        "nota": (
            "Indicadores diagnósticos. Violações de domínio e outliers exigem interpretação humana; "
            "esta etapa não remove registros, não imputa nulos e não altera rótulos. "
            "Outliers por IQR (1,5×) são informativos e não implicam erro."
        ),
    }


def _salvar_json(caminho: Path, conteudo: dict[str, Any]) -> None:
    caminho.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _ambiente() -> dict[str, Any]:
    return {
        "colab": "google.colab" in sys.modules,
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "sistema": platform.platform(),
    }


def _versao_do_caminho(caminho: Path | str) -> int | None:
    """Extrai N de '.../versions/N' (caminho devolvido pelo kagglehub)."""
    achado = re.search(r"versions[/\\](\d+)(?:[/\\]|$)", str(caminho))
    return int(achado.group(1)) if achado else None


def processar_csv(
    origem_csv: Path,
    raiz_destino: Path,
    *,
    referencia_origem: str = DATASET_URL,
    dataset_handle: str = DATASET_HANDLE,
    coletado_em_utc: str | None = None,
    versao_fonte: int | None = None,
    versao_solicitada: int | None = None,
) -> dict[str, Any]:
    """Executa persistência e releitura; é agnóstico quanto ao destino local/Drive.

    A versão publicada do Colab chama esta função com uma pasta no Drive montado.
    Cada execução gera uma subpasta própria para preservar evidências anteriores.
    """
    origem = Path(origem_csv)
    if not origem.is_file():
        raise FileNotFoundError(f"CSV de origem não encontrado: {origem}")
    if origem.suffix.lower() != ".csv":
        raise ValueError(f"Arquivo de origem não é CSV: {origem.name}")

    # Falhar antes da criação do destino se o esquema ou os tipos não servirem.
    bronze_df = ler_csv(origem)
    prata_df = preparar_prata(bronze_df)
    auditoria = auditar_prata(prata_df)

    agora = datetime.now(timezone.utc)
    identificador = agora.strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    pasta_execucao = Path(raiz_destino) / "execucoes" / identificador
    pasta_bronze = pasta_execucao / "bronze"
    pasta_prata = pasta_execucao / "prata"
    pasta_evidencia = pasta_execucao / "evidencias"
    for pasta in (pasta_bronze, pasta_prata, pasta_evidencia):
        pasta.mkdir(parents=True, exist_ok=False)

    bronze_path = pasta_bronze / "Engineering_Cost_Feasibility_Dataset_original.csv"
    prata_path = pasta_prata / "projetos_infraestrutura_flat.csv"
    auditoria_path = pasta_evidencia / "auditoria_qualidade.json"
    manifesto_path = pasta_evidencia / "manifesto_execucao.json"

    # Bronze = bytes originais, não uma reexportação de pandas.
    shutil.copyfile(origem, bronze_path)
    hash_origem = sha256_arquivo(origem)
    hash_bronze = sha256_arquivo(bronze_path)
    if hash_origem != hash_bronze:
        raise AssertionError("SHA-256 da camada bronze difere da origem.")

    prata_df.to_csv(prata_path, index=False, encoding="utf-8", na_rep="")
    hash_prata = sha256_arquivo(prata_path)

    # A validação parte dos arquivos realmente gravados, não de dfs em memória.
    bronze_reaberta = ler_csv(bronze_path)
    prata_reaberta = preparar_prata(ler_csv(prata_path))
    pd.testing.assert_frame_equal(bronze_df, bronze_reaberta, check_dtype=False)
    pd.testing.assert_frame_equal(
        prata_df, prata_reaberta, check_dtype=False, check_exact=False, rtol=1e-12, atol=1e-12,
    )
    if len(prata_reaberta) != len(bronze_reaberta):
        raise AssertionError("Quantidade de registros diverge entre bronze e prata.")
    if hash_prata != sha256_arquivo(prata_path):
        raise AssertionError("Hash da camada prata mudou durante a validação.")

    prata_identica = hash_prata == hash_bronze
    auditoria["validado_apos_releitura"] = True
    _salvar_json(auditoria_path, auditoria)
    manifesto: dict[str, Any] = {
        "status": "concluido_com_releitura",
        "execucao_utc": agora.isoformat(),
        "coletado_em_utc": coletado_em_utc,
        "dataset_handle": dataset_handle,
        "url_fonte": referencia_origem,
        "nome_arquivo_origem": origem.name,
        "formato_original": "CSV (UTF-8, separador vírgula, com cabeçalho)",
        "metadados_fonte": FONTE_METADADOS,
        "licenca_dos_dados": FONTE_METADADOS["licenca"],
        "versao_kaggle_documentada": VERSAO_KAGGLE,
        "versao_kaggle_solicitada": versao_solicitada,
        "versao_kaggle_baixada": versao_fonte,
        "versao_confere": None if versao_fonte is None else versao_fonte == VERSAO_KAGGLE,
        "ambiente": _ambiente(),
        "modelo_dados": "flat; todas as 13 colunas originais, tipos padronizados",
        "transformacoes_prata": [
            {"regra": "Preservar todas as linhas e a ordem original", "altera_conteudo": False},
            {"regra": "Manter as 13 colunas originais, sem renomear, derivar ou descartar", "altera_conteudo": False},
            {"regra": "Tipar colunas de texto como string e numéricas via to_numeric (erro se inválido)", "altera_conteudo": False},
            {"regra": "Sem imputação, deduplicação, padronização de chaves ou conversão de unidade", "altera_conteudo": False},
        ],
        "prata_identica_a_bronze_byte_a_byte": prata_identica,
        "observacao_prata": (
            "A prata não altera o conteúdo: é cópia validada e tipada da bronze (arquivos idênticos "
            "byte a byte). O CSV não preserva tipos; eles constam em esquema_prata."
            if prata_identica else
            "A prata difere da bronze em bytes (formatação numérica ou texto); os valores foram "
            "conferidos após a releitura. Nenhum registro foi alterado ou removido."
        ),
        "esquema_prata": {c: str(t) for c, t in prata_reaberta.dtypes.items()},
        "registros_bronze": int(len(bronze_reaberta)),
        "registros_prata": int(len(prata_reaberta)),
        "colunas_bronze": list(bronze_reaberta.columns),
        "colunas_prata": list(prata_reaberta.columns),
        "tamanho_bytes_fonte": origem.stat().st_size,
        "tamanho_bytes_bronze": bronze_path.stat().st_size,
        "tamanho_bytes_prata": prata_path.stat().st_size,
        "sha256_fonte": hash_origem,
        "sha256_bronze": hash_bronze,
        "sha256_prata": hash_prata,
        "sha256_fonte_confere_com_v1_documentada": hash_origem == SHA256_CSV_V1,
        "releitura_bronze_e_prata": "APROVADA",
        "resumo_qualidade": auditoria["resumo"],
        "destino_execucao": str(pasta_execucao),
        "auditoria_path": str(auditoria_path),
        "limites_da_evidencia": (
            "Este manifesto é gerado pelo código. A persistência no Drive só é comprovada pela "
            "verificação posterior (verificar_persistencia, após remontar o Drive) e pela captura "
            "da pasta no navegador."
        ),
    }
    _salvar_json(manifesto_path, manifesto)
    if not manifesto_path.is_file() or not auditoria_path.is_file():
        raise AssertionError("Não foi possível comprovar a gravação dos documentos de evidência.")

    print(f"VALIDAÇÃO CONCLUÍDA | linhas={len(prata_reaberta)} | colunas={len(prata_reaberta.columns)}")
    print(f"Bronze SHA-256: {hash_bronze}")
    print(f"Prata  SHA-256: {hash_prata}")
    print(f"Violações do domínio esperado: {auditoria['resumo']['total_violacoes_dominio_esperado']}")
    print(f"Execução: {pasta_execucao}")
    return {
        "manifesto": manifesto,
        "auditoria": auditoria,
        "pasta_execucao": str(pasta_execucao),
        "caminho_prata": str(prata_path),
        "caminho_bronze": str(bronze_path),
    }


def verificar_persistencia(pasta_execucao: Path, *, remontado: bool = False) -> dict[str, Any]:
    """Confere, a partir dos ARQUIVOS em disco, o que o manifesto afirma.

    No Colab, chame depois de drive.flush_and_unmount() e drive.mount(..., force_remount=True)
    e passe remontado=True. O parâmetro é uma declaração de quem chama: o código não
    consegue provar sozinho que houve remontagem. Levanta AssertionError se algo divergir
    e grava evidencias/verificacao_persistencia.json se tudo conferir.
    """
    pasta = Path(pasta_execucao)
    evidencias = pasta / "evidencias"
    manifesto = json.loads((evidencias / "manifesto_execucao.json").read_text(encoding="utf-8"))
    auditoria_salva = json.loads((evidencias / "auditoria_qualidade.json").read_text(encoding="utf-8"))
    bronze_path = pasta / "bronze" / "Engineering_Cost_Feasibility_Dataset_original.csv"
    prata_path = pasta / "prata" / "projetos_infraestrutura_flat.csv"
    for caminho in (bronze_path, prata_path):
        if not caminho.is_file():
            raise AssertionError(f"Arquivo ausente na pasta de execução: {caminho}")

    hash_bronze = sha256_arquivo(bronze_path)
    hash_prata = sha256_arquivo(prata_path)
    if hash_bronze != manifesto["sha256_bronze"] or hash_prata != manifesto["sha256_prata"]:
        raise AssertionError("SHA-256 dos arquivos lidos difere do registrado no manifesto.")
    if bronze_path.stat().st_size != manifesto["tamanho_bytes_bronze"]:
        raise AssertionError("Tamanho da bronze difere do manifesto.")
    if prata_path.stat().st_size != manifesto["tamanho_bytes_prata"]:
        raise AssertionError("Tamanho da prata difere do manifesto.")

    prata = preparar_prata(ler_csv(prata_path))
    bronze = ler_csv(bronze_path)
    if len(prata) != manifesto["registros_prata"] or len(bronze) != manifesto["registros_bronze"]:
        raise AssertionError("Número de registros lido difere do manifesto.")
    if list(prata.columns) != manifesto["colunas_prata"]:
        raise AssertionError("Colunas da prata diferem do manifesto.")

    # Refaz a auditoria sobre a prata relida e compara com a auditoria gravada.
    nova = json.loads(json.dumps(auditar_prata(prata), allow_nan=False))
    salva = {k: v for k, v in auditoria_salva.items() if k != "validado_apos_releitura"}
    if nova != salva:
        raise AssertionError("A auditoria refeita sobre a prata relida difere da auditoria gravada.")

    resultado = {
        "verificado_em_utc": datetime.now(timezone.utc).isoformat(),
        "pasta_execucao": str(pasta),
        "remontagem_do_drive_declarada_pelo_chamador": bool(remontado),
        "ambiente": _ambiente(),
        "arquivos": {
            "bronze": {"sha256": hash_bronze, "bytes": bronze_path.stat().st_size, "linhas": int(len(bronze))},
            "prata": {"sha256": hash_prata, "bytes": prata_path.stat().st_size, "linhas": int(len(prata))},
        },
        "sha256_confere_com_manifesto": True,
        "tamanhos_conferem_com_manifesto": True,
        "registros_e_colunas_conferem": True,
        "auditoria_refeita_igual_a_gravada": True,
        "violacoes_dominio_esperado": nova["resumo"]["total_violacoes_dominio_esperado"],
        "resultado": "APROVADA",
        "limite": (
            "Prova que os arquivos lidos agora coincidem com o manifesto. Só indica persistência "
            "na nuvem se executado no Colab após remontar o Drive; complemente com captura da pasta."
        ),
    }
    _salvar_json(evidencias / "verificacao_persistencia.json", resultado)
    print(f"PERSISTÊNCIA VERIFICADA | remontado={remontado} | linhas={len(prata)} | prata SHA-256={hash_prata}")
    return resultado


def executar_pipeline(
    pasta_drive: Path, *, handle: str = DATASET_HANDLE, versao: int = VERSAO_KAGGLE,
) -> dict[str, Any]:
    """Baixa a versão fixada da base do Kaggle e processa no Google Drive montado."""
    raiz_drive = Path("/content/drive/MyDrive")
    if not raiz_drive.is_dir():
        raise RuntimeError("Google Drive não montado. Execute drive.mount('/content/drive') no Colab.")
    destino = Path(pasta_drive).resolve()
    raiz = raiz_drive.resolve()
    if destino != raiz and raiz not in destino.parents:
        raise ValueError("O destino deve estar dentro de /content/drive/MyDrive.")

    import kagglehub

    download = Path(kagglehub.dataset_download(f"{handle}/versions/{versao}"))
    coletado_em = datetime.now(timezone.utc).isoformat()
    candidatos = sorted(download.rglob("*.csv")) if download.is_dir() else [download]
    candidatos = [p for p in candidatos if p.is_file() and p.suffix.lower() == ".csv"]
    if len(candidatos) != 1:
        raise ValueError(f"Era esperado exatamente um CSV; encontrados: {candidatos}")
    return processar_csv(
        candidatos[0], destino, dataset_handle=handle,
        coletado_em_utc=coletado_em, versao_fonte=_versao_do_caminho(download),
        versao_solicitada=versao,
    )
