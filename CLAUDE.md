# Contexto permanente — Claude Code (PSP8 / UnB)

## Objetivo e fonte de verdade
Este repositório é o MVP **Viabilidade de Nova Unidade de Infraestrutura de Dados**, da disciplina **PSP8**, Universidade de Brasília, professor André Luiz Marques Serrano. O projeto deve cumprir o enunciado `TRAB SSD EP UNB.pdf` do professor, que o usuário fornecerá para leitura. **Não presuma que requisitos de outra disciplina substituem esse PDF.**

Arquivos essenciais de planejamento:
- `docs/planejamento_psp8.md`: escopo, arquitetura e quatro perguntas de negócio aprovados pelo usuário.
- `docs/execucao_pipeline_psp8.md`: instruções e pendências reais da implementação em nuvem.
- `README.md` e `MVP_Viabilidade_Nova_Unidade_Dados.ipynb`: MVP original, manter intactos inicialmente.

## Decisões de projeto já validadas
- **Não começar do zero.** Preservar a lógica do MVP de custo, risco e prazo e corrigir documentação, ETL, qualidade, evidências e análises para aderir ao professor.
- Dados: Kaggle `ziya07/engineering-project-cost-feasibility-dataset`, base de infraestrutura genérica (não específica de data centers), com **3.245 registros e 13 colunas na execução observada**.
- O MVP original usa **percentis empíricos** e **média de três dimensões com pesos iguais**; as faixas Favorável/Atenção/Crítica são **heurísticas**, não ML nem probabilidade de inviabilidade.
- Plataforma aprovada: **Google Colab (Python/Pandas) + Google Drive (CSV bronze e prata)**. Drive é armazenamento, não um data warehouse gerenciado.
- Perguntas aprovadas: P1 estatísticas históricas; P2 percentis de um cenário; P3 índice geral e recomendações; P4 análise de sensibilidade/cenários (ainda não implementada).
- Produzir, **após a auditoria final**, um **short paper** acadêmico e uma **apresentação com notas do apresentador**, semelhantes ao trabalho de SSD, mas baseados somente neste MVP.

## Estado verificável (não exagerar)
- Branch atual de trabalho: `psp8-etapa-2-pipeline`, derivada de `psp8-etapa-1-planejamento`. Branch `main` e notebook original preservados.
- Foram criados: `scripts/pipeline_etl_drive.py`, `notebooks/PSP8_Pipeline_Bronze_Prata_Colab.ipynb`, `tests/test_pipeline_etl_drive.py`, `docs/execucao_pipeline_psp8.md`.
- O usuário executou o notebook no Colab; a captura final mostra tabela de **3.245 IDs únicos, 13 colunas e zero nulos por atributo**. **Ainda não foi enviada/verificada a saída completa do manifesto, os hashes nem a pasta bronze/prata/evidências no Drive.**
- **Os testes locais não foram executados/comprovados nesta conversa.** Execute-os e reporte resultados antes de aprovar o pipeline.
- A licença e versão precisa do dataset do Kaggle precisam ser confirmadas na fonte, não presumidas.
- Não declarar persistência comprovada, pipeline aprovado ou perguntas P1–P4 respondidas antes das respectivas evidências.

## Regras obrigatórias de trabalho
1. **Primeira tarefa: auditoria SOMENTE LEITURA** do notebook, script, testes, README e dois documentos acima; localizar bugs, inconsistências, riscos e lacunas versus `TRAB SSD EP UNB.pdf`. Apresentar diagnóstico, severidade e plano mínimo de correção.
2. **Etapas com aprovação explícita:** planejar → implementar → testar → demonstrar evidências → pedir validação. Não avançar automaticamente para short paper ou slides.
3. **Nunca modificar `main`, fazer push, abrir/mesclar PR, apagar dados, reformular as perguntas, mudar pesos/cortes heurísticos ou reescrever notebook original sem aprovação específica.**
4. Em caso de permissão para editar, trabalhar primeiro em arquivos novos e na branch de desenvolvimento. Mostrar diff por arquivo, executar testes e separar achados comprovados de hipóteses.
5. Privacidade: não publicar credenciais, tokens, arquivos privados do Google Drive, dados pessoais ou dados sem licença compatível.
6. Preservar reprodutibilidade: documentar fontes, campos, domínios, transformações, hash, data real da coleta, auditoria por atributo e evidências de persistência no Drive.
7. Usar explicações **em português, diretas, técnicas e didáticas**, sem funcionalidades inventadas nem escrita acadêmica excessiva.
8. **No fim de cada sessão:** indicar o que foi feito, o que foi testado, o que falta, e qual é a próxima validação do usuário.

## Comandos e observações
- Testes propostos: `python -m unittest discover -s tests -v` (requer `pandas`).
- O Colab é o ambiente autorizado para executar `drive.mount('/content/drive')`; execução local ou testes sintéticos **não comprovam** armazenamento na nuvem.
- Consulte `docs/planejamento_psp8.md` antes de propor mudanças metodológicas.
