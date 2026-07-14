# Mapa de Carga Horária — Cálculo de Proventos (Aposentadoria)

Aplicativo web para **gerar o Mapa de Carga Horária** de docentes (professores) da rede
estadual de ensino de São Paulo, conforme o **ANEXO III — SEDUC / DIPES / CEVIF**, usado no
cálculo de proventos de aposentadoria.

O app automatiza o preenchimento e os cálculos do formulário oficial descrito no manual de
orientação, dispensando o preenchimento manual e reduzindo erros de conta.

## Versões disponíveis

- **Web** (esta pasta): abre no navegador, sem instalação — veja instruções abaixo.
- **Desktop nativo para PC** (pasta [`desktop/`](desktop/)): aplicativo em Python/Tkinter que
  pode ser distribuído como **executável único** (`.exe` no Windows) via PyInstaller.
  Consulte [`desktop/README.md`](desktop/README.md).

## Funcionalidades

- **Identificação do docente** (campos 1 a 6): nome, RG, CPF, cargo/função, faixa/nível, DI,
  vínculo (Titular de Cargo ou OFA) e jornada atual.
- **Tabela de carga horária mensal** (campo 7): montada automaticamente por ano/mês a partir do
  mês final e do período de opção escolhido.
- **Períodos de opção** previstos no manual:
  - **60 meses** — últimos 60 meses (regra geral, A1/B);
  - **84 meses ininterruptos** (A2);
  - **120 meses intercalados** (A2).
- **Cálculo automático**:
  - Totais anuais e **Total Geral da Carga Horária** (campo 7.A);
  - **Média da Carga Horária** (campo 10) = Total Geral ÷ nº de meses da opção, **arredondada ao
    inteiro**;
  - Desdobramento em **Jornada + Carga Suplementar** conforme as regras do campo 10.
- **Preenchimento rápido**: aplica um mesmo valor de horas a todos os meses do período.
- **Impressão / PDF** com layout próximo ao formulário oficial (use "Imprimir" → "Salvar como PDF").
- **Salvamento automático** no navegador (localStorage) e botão para carregar um **exemplo**.

## Regras de cálculo implementadas (campo 10)

Baseadas no manual (LC 836/97, Art. 39 das DDTT):

- **Titular de Cargo**: preenche os 3 campos (Média, Jornada e Carga Suplementar).
  - Se a **Média for menor que a Jornada** atual, preenche **apenas** o 1º campo (Média).
  - Caso contrário: `Carga Suplementar = Média − Jornada`.
- **Ocupante de Função-Atividade (OFA)**: preenche **somente** o 1º campo (Média).

Jornadas do PEB consideradas: Reduzida (96h), Inicial (120h), Básica (150h) e Completa (200h).

> **Observações do manual** já embutidas na saída: verificar sempre a SED para evitar divergências;
> equivalência entre horas e horas-aula para períodos anteriores a 01/02/1998 (Anexo I), exceto em
> regime de 40 horas; e a nota do PA SPPREV nº 756/2015 / Informação UCRH nº 246/2016.

## Como usar

Não requer instalação nem build — é HTML/CSS/JS puro.

1. Abra o arquivo `index.html` no navegador, **ou** sirva a pasta localmente:
   ```bash
   python3 -m http.server 8000
   # depois acesse http://localhost:8000
   ```
2. Preencha os dados do docente, escolha o vínculo, a jornada e o período de opção.
3. Informe o **mês/ano final** do período; a tabela mensal é gerada automaticamente.
4. Preencha a carga horária de cada mês (ou use o preenchimento rápido).
5. Confira o mapa gerado à direita e clique em **Imprimir / PDF**.

## Estrutura

```
index.html      # estrutura da página e formulário
css/styles.css  # estilos (tela e impressão)
js/app.js       # estado, cálculos e renderização do mapa
```

## Base legal / referências

- LC 836/97 — Art. 39 das Disposições Transitórias (DDTT)
- PA SPPREV nº 756/2015 · Informação UCRH nº 246/2016
- Homologação: **CEVIF** — `cevif@educacao.sp.gov.br`

> Ferramenta de apoio ao preenchimento. Os dados devem sempre ser conferidos na **SED/GDAE** antes
> do envio para homologação.
