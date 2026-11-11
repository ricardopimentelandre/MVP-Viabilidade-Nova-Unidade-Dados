# Etapa 2 — Pipeline de dados em nuvem (instruções de validação)

Este documento complementa [o planejamento aprovado](planejamento_psp8.md). **O desenvolvimento do código não equivale à comprovação de execução no Google Drive.** O usuário valida cada etapa antes de promover mudanças para `main`.

## Arquivos criados

- [`scripts/pipeline_etl_drive.py`](../scripts/pipeline_etl_drive.py): coleta com KaggleHub, preservação de CSV original, transformação tipada, auditoria dos 13 atributos, exportação e releitura do Drive, SHA-256 e manifesto.
- [`notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb`](../notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb): execução guiada no Google Colab.
- [`tests/test_pipeline_etl_drive.py`](../tests/test_pipeline_etl_drive.py): testes de unidade com dados artificiais; não requer acesso ao Kaggle ou Drive.

O notebook inicial [`MVP_Viabilidade_Nova_Unidade_Dados.ipynb`](../MVP_Viabilidade_Nova_Unidade_Dados.ipynb) permanece intacto. As análises P1–P4 e a integração delas à prata serão tratadas somente nas próximas etapas.

## Execução no Google Colab

1. Abra o arquivo `notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb` no Colab.
2. Execute a instalação de `kagglehub` e `pandas`.
3. Execute `drive.mount('/content/drive')` e autorize **seu próprio Drive**.
4. Execute a célula que baixa o script versionado da branch de trabalho.
5. Execute `executar_pipeline`; a fonte do Kaggle é baixada e a pasta no Google Drive é criada.
6. Execute as células de verificação do manifesto, dos hashes e da tabela prata relida.
7. Inspecione `MyDrive/UnB/PSP8/MVP_Viabilidade_Nova_Unidade/execucoes/<id>/`.

Estrutura esperada:

```text
execucoes/<id>/
  bronze/
    Engineering_Cost_Feasibility_Dataset_original.csv
  prata/
    projetos_infraestrutura_flat.csv
  evidencias/
    manifesto_execucao.json
    auditoria_qualidade.json
```

Os arquivos JSON da pasta `evidencias` registram os resultados do código; **não** substituem uma captura legível da pasta no Drive e das verificações do notebook.

## Validações para esta etapa

- **Origem:** conferir na página do Kaggle a licença, atualização e possibilidade de redistribuição do dataset; o código **não presume licença** e marca `PENDENTE_DE_CONFIRMACAO_NA_FONTE`.
- **Esquema:** 13 colunas esperadas; o código falha se faltar ou sobrar uma coluna. Para a fonte original conhecida, eram 3.245 registros, mas o pipeline não força o número: qualquer mudança deverá ser analisada.
- **Bronze:** bytes do arquivo original são copiados sem edição. Hash do arquivo original = hash da cópia.
- **Prata:** modelo *flat* com 13 colunas, tipagem explícita e sem remoção ou imputação. A ordem das linhas é mantida.
- **Qualidade:** auditar nulos, unicidade, duplicatas, extremos e domínios numéricos; verificar concordância básica entre complexidade categórica e numérica. Valores sinalizados precisam de interpretação na próxima etapa.
- **Releitura:** após gravar, o Python lê novamente bronze e prata do Drive e compara com os dados em memória. Hash e manifesto documentam integridade.
- **Segurança:** o Drive é privado; não publicar tokens, credenciais ou dados sem verificar a licença.

> Os limites de 0 a 100 adotados para os atributos de escore são *checagens exploratórias*; o domínio definitivo será confirmado no catálogo e na fonte. A classificação original de viabilidade não é uma verdade de campo nem um resultado de previsão.

## Testes independentes da nuvem

Na raiz do repositório, com `pandas` instalado:

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem preservação do arquivo bruto, leitura e auditoria da prata, registros repetidos e rejeição de esquemas/tipos inválidos. Testes locais bem-sucedidos **não comprovam a persistência no Google Drive**.

## Pendências explícitas (não considerar concluídas)

- [ ] Executar o notebook no Colab com a conta Google do usuário.
- [ ] Confirmar a pasta, os arquivos, as contagens e os SHA-256 no Drive.
- [ ] Verificar licença da fonte e registrar exatamente a licença e a data real da coleta.
- [ ] Capturar e versionar evidências legíveis da execução em nuvem.
- [ ] Executar testes locais em ambiente com dependências, registrando o resultado.
- [ ] Revisar com o usuário os resultados da auditoria de cada atributo.
- [ ] Desenvolver as perguntas de negócio P1–P4 **a partir da prata relida**.
- [ ] Criar catálogo de dados definitivo, README de entrega e autoavaliação.

**Não mesclar esta branch na `main` antes da aprovação e validação das pendências.**
