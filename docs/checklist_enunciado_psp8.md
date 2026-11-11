# Checklist do enunciado (`TRAB SSD EP UNB.pdf`) — requisito por requisito

Situação em 11/11/2026. **Atendido** = comprovado no repositório; **Atendido, falta evidência** = executado conforme relato do autor, mas sem captura anexada; **Pendente** = depende de ação do autor.

## Checklist de entrega (§8)

| # | Requisito | Situação | Onde |
|---|---|---|---|
| 1 | Objetivo e perguntas de negócio documentados e íntegros, inclusive os não atingidos | **Atendido** (P1–P4 íntegras; hipótese e critério de refutação) | README §1; `docs/planejamento_psp8.md` |
| 2 | Origem, licença e data de coleta registradas | **Atendido** (Kaggle v1, CC0, execução de 11/11/2026). *Reconfirmar a licença na página do dataset* | README §2; manifesto; catálogo §1 |
| 3 | Dados efetivamente persistidos na nuvem | **Atendido**: pipeline executado no Colab com Drive desmontado/remontado e `APROVADA` (capturas 01, 02, 03) e os três JSONs no Drive (captura 06). Falta só a captura 05 (pasta da execução com `bronze/` e `prata/`) | README §5 e §10; `evidencias/capturas/` |
| 4 | Modelo descrito e Catálogo com domínios e linhagem | **Atendido** (13 atributos, tipo, descrição, domínio, obrigatoriedade, linhagem, diagramas) | `catalogo/catalogo_dados.md` |
| 5 | Transformação e carga documentadas, com regras de negócio explícitas | **Atendido** (nenhuma transformação de conteúdo, declarada; prata idêntica à bronze) | README §5; manifesto `transformacoes_prata` |
| 6 | Análise de qualidade cobre todos os atributos | **Atendido** (13 atributos × completude, unicidade, conformidade, consistência, acurácia, atualidade) | README §6; `auditoria_qualidade.json` |
| 7 | Cada pergunta com resposta, evidência e discussão | **Atendido**: P1–P4 respondidas no README e no notebook; **7 gráficos reais do Colab anexados** em `evidencias/graficos/` e referenciados na seção 7 | README §7; `notebooks/PSP8_Analise_P1_P4.ipynb`; `evidencias/graficos/` |
| 8 | Discussão geral conectando as respostas ao problema | **Atendido** | README §8; notebook (discussão geral) |
| 9 | Autoavaliação com as 4 questões sugeridas (§6) | **Atendido** | README §11 |
| 10 | Evidências (capturas e vídeos) legíveis e referenciadas | **Quase completo**: 5 capturas (01–04 e 06) e 7 gráficos anexados e referenciados no README; **falta a captura 05** (pasta da execução no Drive) | `evidencias/capturas/`, `evidencias/graficos/` |
| 11 | Repositório público, link conferido em janela anônima | **Atendido**: conferido pelo autor em janela anônima (captura não publicada) e `private: false` na API do GitHub. Falta postar o link no fórum | — |

## Demais requisitos do enunciado

| Seção | Requisito | Situação |
|---|---|---|
| §2.2 | 3 a 6 perguntas, definidas antes dos dados | **Parcial, declarado**: 4 perguntas; o protótipo e a base precederam a formalização, e isso consta no README §1 e na autoavaliação |
| §2.3 | Dados persistidos na nuvem e demonstráveis | Ver item 3 |
| §3.2 | Data da coleta, volume e formato original | **Atendido** (11/11/2026; 261.932 bytes, 3.245 × 13; CSV UTF-8) |
| §3.3 | Catálogo: nome, tipo, descrição, domínio (mín/máx e categorias), obrigatoriedade, linhagem | **Atendido** |
| §3.4 | ETL documentado; regras de transformação explícitas | **Atendido** |
| §3.5a | Qualidade por atributo, inclusive "sem problemas" demonstrado | **Atendido** |
| §3.5b | Resposta e discussão por pergunta; resultados negativos relatados | **Atendido** (resultado negativo de P3 destacado) |
| §4 | Licença, uso derivado, não versionar dados se necessário, LGPD | **Atendido**: CC0, dados não versionados, sem dados pessoais. A licença deve ser reconfirmada na página |
| §5.1 | `README.md`, `/notebooks`, `/scripts`, `/catalogo`, `/evidencias` | **Atendido** (a pasta `/evidencias` ainda sem imagens) |
| §5.1 | `LICENSE` (licença do código e registro da licença dos dados) | **Atendido**: MIT para o código (© 2026 Ricardo Pimentel André) e registro da licença CC0 dos dados |
| §5.3 | Postagem do link no fórum da disciplina | **Pendente** (ação do autor) |

## Rubrica (§7)

| Critério | Pts | Situação |
|---|---|---|
| Objetivo | 1,0 | Completo |
| Coleta | 0,5 | Completo (reconfirmar licença na página) |
| Modelagem (modelo + catálogo) | 2,0 | Completo |
| Carga | 1,0 | Completa; persistência comprovada nas capturas 01–03 e 06 (falta só a 05) |
| Análise (qualidade, solução, discussão) | 3,0 | Completa, com gráficos reais anexados |
| Autoavaliação | 0,5 | Completa |
| Capricho | 2,0 | README e repositório organizados, gráficos anexados; a **captura 05** completa as evidências |
