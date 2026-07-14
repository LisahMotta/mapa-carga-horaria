# Mapa de Carga Horária — App Desktop (Python / Tkinter)

Aplicativo **nativo para PC** (Windows, Linux e macOS) que gera o **Mapa de Carga Horária**
de docente para aposentadoria — ANEXO III · SEDUC / DIPES / DVIF.

Mesma lógica da versão web, porém rodando como programa de desktop, sem depender de navegador,
e podendo ser distribuído como **executável único** (`.exe` no Windows).

## Recursos

- Formulário completo (campos 1 a 10) com identificação, vínculo (Titular/OFA) e jornada.
- Tabela de carga horária mensal gerada automaticamente por ano/mês.
- Períodos de opção: **60**, **84 (ininterruptos)** e **120 (intercalados)** meses.
- Cálculo automático do **Total Geral (7.A)** e da **Média (campo 10)**, com desdobramento
  em **Jornada + Carga Suplementar** conforme as regras do manual.
- **Salvar / Abrir** mapas em arquivo `.json`.
- **Exportar / Imprimir**: gera um HTML pronto para impressão e o abre no navegador
  (use "Imprimir" → "Salvar como PDF").
- **Baixar Excel (.xlsx)**: gera o mapa em planilha do Excel, com o layout do formulário
  oficial ANEXO III (quadro anual, TOTAIS, 7.A, campo 8, declaração e campo 10), pronta
  para conferir e imprimir no Excel.
- **Calculadora — carga horária quebrada no mês**: para períodos inferiores a um mês
  (Jornada ÷ 30 × nº de dias), com opção de somar dois períodos.
- Botão **Exemplo** e **Preenchimento rápido**.

## Executar a partir do código-fonte

Requer **Python 3.10+** com **tkinter** (incluso no instalador oficial do python.org) e a
biblioteca **openpyxl** (para a exportação em Excel).

```bash
pip install -r requirements.txt   # instala openpyxl (e pyinstaller)
# Linux (tkinter pode precisar ser instalado):
#   Ubuntu/Debian: sudo apt install python3-tk
#   Fedora:        sudo dnf install python3-tkinter
python3 mapa_carga_horaria.py
```

No Windows, basta ter o Python instalado e dar duplo clique em `mapa_carga_horaria.py`
(ou `python mapa_carga_horaria.py`).

## Baixar o `.exe` pronto (Windows) — sem instalar nada

Um workflow do GitHub Actions compila o executável automaticamente em um runner Windows.
Para baixar o `.exe` já pronto:

1. No GitHub, abra a aba **Actions** → workflow **"Build Windows EXE"**.
2. Clique na execução mais recente (verde ✔).
3. Na seção **Artifacts**, baixe **`MapaCargaHoraria-windows`** (um `.zip`).
4. Extraia e execute **`MapaCargaHoraria.exe`** — não requer Python instalado.

> Para disparar manualmente: aba **Actions** → **Build Windows EXE** → **Run workflow**.
> Ao publicar uma tag `v*` (ex.: `v1.0`), o `.exe` também é anexado a uma **Release**.

## Gerar o executável localmente (`dist/`)

O empacotamento usa **PyInstaller** e produz um executável único.

### Windows → `dist\MapaCargaHoraria.exe`

```bat
build.bat
```

> ⚠️ Um `.exe` do Windows **precisa ser gerado em um PC Windows** (o PyInstaller não faz
> cross-compilação). Rode o `build.bat` na máquina Windows onde o app será usado.

### Linux / macOS → `dist/MapaCargaHoraria`

```bash
./build.sh
```

### Manualmente (qualquer sistema)

```bash
pip install -r requirements.txt
pyinstaller mapa.spec
```

O resultado fica na pasta `dist/`. É um arquivo autônomo — não exige Python instalado na
máquina de destino.

## Testes

A lógica de cálculo tem testes automatizados (independentes da interface):

```bash
python -m unittest test_calculo -v
```

## Arquivos

```
mapa_carga_horaria.py  # aplicativo (interface Tkinter)
calculo.py             # lógica de cálculo (sem dependência de GUI)
excel_export.py        # geração do Mapa em Excel (.xlsx) no layout oficial
test_calculo.py        # testes automatizados da lógica
mapa.spec              # configuração do PyInstaller
build.bat / build.sh   # scripts de geração do executável
requirements.txt       # dependência de build (pyinstaller)
```

## Base legal / referências

LC 836/97 (Art. 39 das DDTT) · PA SPPREV nº 756/2015 · Informação UCRH nº 246/2016.
Homologação: **DVIF**. Sempre conferir os dados na **SED/GDAE**.
