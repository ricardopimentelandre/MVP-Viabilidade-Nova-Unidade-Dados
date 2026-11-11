"""ETL auditável: Kaggle -> Colab/Pandas -> Google Drive (bronze e prata).

A execução real no Drive deve ser feita pelo notebook Colab. Este módulo também
expõe processar_csv() para testes locais sem Kaggle, autenticação ou rede.
Os dados não são publicados no GitHub.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

DATASET_HANDLE = "ziya07/engineering-project-cost-feasibility-dataset"
DATASET_URL = "https://www.kaggle.com/datasets/ziya07/engineering-project-cost-feasibility-dataset"

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
COLUNAS_SCORE_0_100 = [
    "Resource_Allocation_Score", "Risk_Assessment_Score",
    "Environmental_Impact_Score", "Stakeholder_Priority_Score",
]


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
        float_precision="round_trip",
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


def _numero_ou_nulo(valor: Any) -> float | int | None:
    if pd.isna(valor):
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    return float(valor)


def auditar_prata(prata: pd.DataFrame) -> dict[str, Any]:
    """Auditoria diagnóstica por atributo. Não corrige registros silenciosamente."""
    validar_esquema(prata)
    atributos: dict[str, dict[str, Any]] = {}
    for coluna in COLUNAS_ESPERADAS:
        serie = prata[coluna]
        dados: dict[str, Any] = {
            "tipo_pandas": str(serie.dtype),
            "nulos": int(serie.isna().sum()),
            "valores_unicos": int(serie.nunique(dropna=True)),
            "duplicados_na_coluna": int(serie.duplicated(keep="first").sum()),
        }
        if coluna in COLUNAS_NUMERICAS:
            n = pd.to_numeric(serie, errors="coerce")
            dados.update({
                "minimo_observado": _numero_ou_nulo(n.min()),
                "maximo_observado": _numero_ou_nulo(n.max()),
                "negativos": int((n < 0).sum()),
                "nao_finitos": int((~n.dropna().map(lambda x: bool(pd.notna(x)) and abs(float(x)) != float("inf"))).sum()),
            })
            if coluna in COLUNAS_SCORE_0_100:
                dados["fora_0_a_100"] = int(((n < 0) | (n > 100)).sum())
        else:
            normalizado = serie.astype("string")
            dados["vazios_ou_espacos"] = int(normalizado.fillna("").str.strip().eq("").sum())
            dados["categorias_mais_frequentes"] = {
                str(chave): int(valor)
                for chave, valor in normalizado.value_counts(dropna=False).head(12).items()
            }
        atributos[coluna] = dados

    ids_duplicados = int(prata["Project_ID"].duplicated(keep="first").sum())
    linhas_duplicadas = int(prata.duplicated(keep="first").sum())
    pares = (
        prata[["Scope_Complexity", "Scope_Complexity_Numeric"]]
        .dropna().drop_duplicates()
    )
    categorias_com_multiplos_codigos = int(
        (pares.groupby("Scope_Complexity")["Scope_Complexity_Numeric"].nunique() > 1).sum()
    )
    codigos_com_multiplas_categorias = int(
        (pares.groupby("Scope_Complexity_Numeric")["Scope_Complexity"].nunique() > 1).sum()
    )
    return {
        "linhas": int(len(prata)),
        "colunas": int(len(prata.columns)),
        "linhas_duplicadas_exatas": linhas_duplicadas,
        "project_id_duplicados": ids_duplicados,
        "inconsistencias_categoria_para_codigo_complexidade": categorias_com_multiplos_codigos,
        "inconsistencias_codigo_para_categoria_complexidade": codigos_com_multiplas_categorias,
        "atributos": atributos,
        "nota": (
            "Indicadores diagnósticos; valores fora de faixa exigem interpretação. "
            "Esta etapa não remove registros, não imputa nulos e não altera rótulos."
        ),
    }


def _salvar_json(caminho: Path, conteudo: dict[str, Any]) -> None:
    caminho.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def processar_csv(
    origem_csv: Path,
    raiz_destino: Path,
    *,
    referencia_origem: str = DATASET_URL,
    dataset_handle: str = DATASET_HANDLE,
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

    coleta_em_utc = datetime.now(timezone.utc).isoformat()
    identificador = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
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

    auditoria["validado_apos_releitura"] = True
    _salvar_json(auditoria_path, auditoria)
    manifesto: dict[str, Any] = {
        "status": "concluido_com_releitura",
        "execucao_utc": coleta_em_utc,
        "dataset_handle": dataset_handle,
        "url_fonte": referencia_origem,
        "nome_arquivo_origem": origem.name,
        "licenca_dos_dados": "PENDENTE_DE_CONFIRMACAO_NA_FONTE",
        "versao_kaggle": "nao_fixada_no_handle; rastrear_por_sha256",
        "plataforma_processamento": "Python/Pandas (execucao Colab deve ser comprovada)",
        "modelo_dados": "flat; todas as 13 colunas originais, tipos padronizados",
        "regras": ["preservar linhas e ordem", "preservar CSV bruto byte a byte", "converter colunas numericas sem imputar ou excluir registros"],
        "registros_bronze": int(len(bronze_reaberta)),
        "registros_prata": int(len(prata_reaberta)),
        "colunas_bronze": list(bronze_reaberta.columns),
        "colunas_prata": list(prata_reaberta.columns),
        "sha256_fonte": hash_origem,
        "sha256_bronze": hash_bronze,
        "sha256_prata": hash_prata,
        "releitura_bronze_e_prata": "APROVADA",
        "destino_execucao": str(pasta_execucao),
        "auditoria_path": str(auditoria_path),
        "observacao": "A execução e as capturas no Drive devem ser conferidas antes da entrega acadêmica.",
    }
    _salvar_json(manifesto_path, manifesto)
    if not manifesto_path.is_file() or not auditoria_path.is_file():
        raise AssertionError("Não foi possível comprovar a gravação dos documentos de evidência.")

    print(f"VALIDAÇÃO CONCLUÍDA | linhas={len(prata_reaberta)} | colunas={len(prata_reaberta.columns)}")
    print(f"Bronze SHA-256: {hash_bronze}")
    print(f"Prata  SHA-256: {hash_prata}")
    print(f"Execução: {pasta_execucao}")
    return {
        "manifesto": manifesto,
        "auditoria": auditoria,
        "pasta_execucao": str(pasta_execucao),
        "caminho_prata": str(prata_path),
        "caminho_bronze": str(bronze_path),
    }


def executar_pipeline(pasta_drive: Path, *, handle: str = DATASET_HANDLE) -> dict[str, Any]:
    """Baixa a base do Kaggle e processa no Google Drive montado pelo Colab."""
    raiz_drive = Path("/content/drive/MyDrive")
    if not raiz_drive.is_dir():
        raise RuntimeError("Google Drive não montado. Execute drive.mount('/content/drive') no Colab.")
    destino = Path(pasta_drive).resolve()
    raiz = raiz_drive.resolve()
    if destino != raiz and raiz not in destino.parents:
        raise ValueError("O destino deve estar dentro de /content/drive/MyDrive.")

    import kagglehub

    download = Path(kagglehub.dataset_download(handle))
    candidatos = sorted(download.rglob("*.csv")) if download.is_dir() else [download]
    candidatos = [p for p in candidatos if p.is_file() and p.suffix.lower() == ".csv"]
    if len(candidatos) != 1:
        raise ValueError(f"Era esperado exatamente um CSV; encontrados: {candidatos}")
    return processar_csv(candidatos[0], destino, dataset_handle=handle)
