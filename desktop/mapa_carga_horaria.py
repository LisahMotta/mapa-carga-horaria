#!/usr/bin/env python3
"""
Mapa de Carga Horária — Cálculo de Proventos (Aposentadoria)
Aplicativo desktop nativo (Tkinter) — ANEXO III · SEDUC / DIPES / DVIF.

Gera o Mapa de Carga Horária de docente para aposentadoria, com preenchimento
mensal, cálculo automático da média e exportação para HTML (impressão/PDF).
"""

from __future__ import annotations

import json
import os
import tempfile
import webbrowser
from datetime import date
from tkinter import (
    Tk, StringVar, IntVar, Text, filedialog, messagebox, ttk, Canvas, Frame,
    N, S, E, W, END,
)

from calculo import (
    MESES, JORNADAS, PERIODOS, chave, periodo_meses, anos_do_periodo, calcular,
)

APP_TITULO = "Mapa de Carga Horária — Cálculo de Proventos"


def mes_final_padrao() -> str:
    """Mês anterior ao atual, no formato MM/AAAA."""
    hoje = date.today()
    ano, mes = hoje.year, hoje.month - 1
    if mes < 1:
        mes = 12
        ano -= 1
    return f"{mes:02d}/{ano}"


class MapaApp(ttk.Frame):
    def __init__(self, master: Tk):
        super().__init__(master, padding=0)
        self.master = master
        self.grid(row=0, column=0, sticky=(N, S, E, W))
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)

        # ----- estado -----
        self.ch: dict[str, float] = {}
        self.cell_vars: dict[str, StringVar] = {}
        self.total_ano_labels: dict[int, ttk.Label] = {}

        self.var_nome = StringVar()
        self.var_rg = StringVar()
        self.var_cpf = StringVar()
        self.var_cargo = StringVar(value="PEB")
        self.var_faixa = StringVar()
        self.var_di = StringVar()
        self.var_vinculo = StringVar(value="titular")
        self.var_jornada = IntVar(value=150)
        self.var_desde = StringVar()
        self.var_doe = StringVar()
        self.var_periodo = IntVar(value=60)
        self.var_mesfinal = StringVar(value=mes_final_padrao())
        self.var_fill = StringVar()
        self.var_calc_jornada = StringVar(value="150")
        self.var_calc_dias = StringVar()
        self.var_calc_jornada2 = StringVar()
        self.var_calc_dias2 = StringVar()

        self._construir()
        self._montar_tabela()
        self._atualizar_resultado()

    # ------------------------------------------------------------------ UI
    def _construir(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Cabeçalho
        head = Frame(self, bg="#1f4e79")
        head.grid(row=0, column=0, sticky=(E, W))
        ttk.Label(
            head, text="Mapa de Carga Horária",
            background="#1f4e79", foreground="white",
            font=("Segoe UI", 15, "bold"),
        ).pack(side="left", padx=14, pady=(10, 0), anchor="w")
        ttk.Label(
            head, text="ANEXO III · SEDUC / DIPES / DVIF — cálculo de proventos",
            background="#1f4e79", foreground="#d6e2ef", font=("Segoe UI", 9),
        ).pack(side="left", padx=8, pady=(14, 8))

        # Barra de ações
        bar = ttk.Frame(self, padding=(10, 8))
        bar.grid(row=1, column=0, sticky=(E, W))
        ttk.Button(bar, text="Novo", command=self.novo).pack(side="left", padx=2)
        ttk.Button(bar, text="Abrir…", command=self.abrir).pack(side="left", padx=2)
        ttk.Button(bar, text="Salvar…", command=self.salvar).pack(side="left", padx=2)
        ttk.Button(bar, text="Exemplo", command=self.carregar_exemplo).pack(side="left", padx=2)
        ttk.Button(bar, text="Exportar / Imprimir (HTML/PDF)", command=self.exportar_html).pack(side="left", padx=(8, 2))
        ttk.Button(bar, text="Baixar Excel (.xlsx)", command=self.exportar_excel).pack(side="left", padx=2)

        # Corpo com duas colunas: formulário (scroll) + resultado
        corpo = ttk.Panedwindow(self, orient="horizontal")
        corpo.grid(row=2, column=0, sticky=(N, S, E, W))

        esq = self._painel_scroll(corpo)
        corpo.add(esq["outer"], weight=3)
        self._construir_formulario(esq["inner"])

        dir_ = ttk.Frame(corpo, padding=12)
        corpo.add(dir_, weight=2)
        self._construir_resultado(dir_)

    def _painel_scroll(self, parent):
        outer = ttk.Frame(parent)
        canvas = Canvas(outer, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas, padding=12)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)) if e.delta else (-1 if e.num == 4 else 1), "units")
        canvas.bind_all("<MouseWheel>", _wheel)
        canvas.bind_all("<Button-4>", _wheel)
        canvas.bind_all("<Button-5>", _wheel)
        return {"outer": outer, "inner": inner}

    def _secao(self, parent, titulo):
        ttk.Label(parent, text=titulo, font=("Segoe UI", 10, "bold"),
                  foreground="#16334f").grid(sticky="w", pady=(12, 4), columnspan=4)

    def _construir_formulario(self, f):
        for c in range(4):
            f.columnconfigure(c, weight=1)
        r = 0

        def campo(label, var, col, span=1, width=None):
            nonlocal r
            cell = ttk.Frame(f)
            cell.grid(row=r, column=col, columnspan=span, sticky=(E, W), padx=4, pady=3)
            cell.columnconfigure(0, weight=1)
            ttk.Label(cell, text=label, font=("Segoe UI", 8)).grid(sticky="w")
            e = ttk.Entry(cell, textvariable=var)
            e.grid(sticky=(E, W))
            var.trace_add("write", lambda *a: self._atualizar_resultado())
            return e

        self._secao(f, "1–4 · Identificação do docente")
        r += 1
        campo("Nome completo (1)", self.var_nome, 0, span=4)
        r += 1
        campo("RG (2)", self.var_rg, 0, span=2)
        campo("CPF (2)", self.var_cpf, 2, span=2)
        r += 1
        campo("Cargo/Função (3)", self.var_cargo, 0)
        campo("Faixa/Nível (4)", self.var_faixa, 1)
        campo("DI (4)", self.var_di, 2)
        r += 1

        self._secao(f, "5–6 · Vínculo e jornada")
        r += 1
        vwrap = ttk.Frame(f)
        vwrap.grid(row=r, column=0, columnspan=2, sticky="w", padx=4)
        ttk.Label(vwrap, text="Vínculo (5)", font=("Segoe UI", 8)).grid(sticky="w", columnspan=2)
        ttk.Radiobutton(vwrap, text="Titular de Cargo", value="titular",
                        variable=self.var_vinculo, command=self._atualizar_resultado).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(vwrap, text="OFA", value="ofa",
                        variable=self.var_vinculo, command=self._atualizar_resultado).grid(row=1, column=1, sticky="w")
        jwrap = ttk.Frame(f)
        jwrap.grid(row=r, column=2, columnspan=2, sticky=(E, W), padx=4)
        jwrap.columnconfigure(0, weight=1)
        ttk.Label(jwrap, text="Jornada atual (6)", font=("Segoe UI", 8)).grid(sticky="w")
        self.cbo_jornada = ttk.Combobox(jwrap, state="readonly",
                                         values=[f"{n} — {h} horas" for h, n in JORNADAS.items()])
        self.cbo_jornada.grid(sticky=(E, W))
        self.cbo_jornada.set(f"{JORNADAS[150]} — 150 horas")
        self.cbo_jornada.bind("<<ComboboxSelected>>", lambda e: self._on_jornada())
        r += 1
        campo("Incluído a partir de (6) — DD/MM/AAAA", self.var_desde, 0, span=2)
        campo("Publicação DOE (6) — DD/MM/AAAA", self.var_doe, 2, span=2)
        r += 1

        self._secao(f, "8 · Nomeação/Designação em regime de 40 horas/semanais")
        r += 1
        ttk.Label(f, text="Diretor, Vice-Diretor, Coordenador (períodos e DOE):",
                  font=("Segoe UI", 8)).grid(row=r, column=0, columnspan=4, sticky="w", padx=4)
        r += 1
        self.txt_nomeacao = Text(f, height=3, wrap="word", font=("Segoe UI", 9),
                                 relief="solid", borderwidth=1)
        self.txt_nomeacao.grid(row=r, column=0, columnspan=4, sticky=(E, W), padx=4, pady=(2, 4))
        self.txt_nomeacao.bind("<KeyRelease>", lambda e: self._atualizar_resultado())
        r += 1

        self._secao(f, "7–9 · Período de opção e carga horária")
        r += 1
        pwrap = ttk.Frame(f)
        pwrap.grid(row=r, column=0, columnspan=2, sticky=(E, W), padx=4)
        pwrap.columnconfigure(0, weight=1)
        ttk.Label(pwrap, text="Período de opção (9)", font=("Segoe UI", 8)).grid(sticky="w")
        self.cbo_periodo = ttk.Combobox(pwrap, state="readonly", values=list(PERIODOS.values()))
        self.cbo_periodo.grid(sticky=(E, W))
        self.cbo_periodo.set(PERIODOS[60])
        self.cbo_periodo.bind("<<ComboboxSelected>>", lambda e: self._on_periodo())
        campo("Mês/ano final (MM/AAAA)", self.var_mesfinal, 2, span=2)
        self.var_mesfinal.trace_add("write", lambda *a: self._montar_tabela())
        r += 1
        fillwrap = ttk.Frame(f)
        fillwrap.grid(row=r, column=0, columnspan=4, sticky=(E, W), padx=4, pady=(2, 6))
        ttk.Label(fillwrap, text="Preenchimento rápido — horas/mês:", font=("Segoe UI", 8)).pack(side="left")
        ttk.Entry(fillwrap, textvariable=self.var_fill, width=8).pack(side="left", padx=6)
        ttk.Button(fillwrap, text="Aplicar a todos", command=self.preencher_todos).pack(side="left")
        r += 1

        self._secao(f, "🧮 Calculadora — carga horária quebrada no mês")
        r += 1
        ttk.Label(f, text="Período inferior a um mês (admissão/exoneração/mudança de jornada). "
                          "Fórmula: (Jornada ÷ 30) × nº de dias. Preencha o Período 2 para somar dois períodos.",
                  font=("Segoe UI", 8), foreground="#5b6675", wraplength=520, justify="left").grid(
            row=r, column=0, columnspan=4, sticky="w", padx=4)
        r += 1
        calcwrap = ttk.Frame(f)
        calcwrap.grid(row=r, column=0, columnspan=4, sticky=(E, W), padx=4, pady=(4, 2))
        ttk.Label(calcwrap, text="Período 1 — Jornada:", font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w")
        ttk.Entry(calcwrap, textvariable=self.var_calc_jornada, width=7).grid(row=0, column=1, padx=(4, 12))
        ttk.Label(calcwrap, text="Nº dias (1–30):", font=("Segoe UI", 8)).grid(row=0, column=2, sticky="w")
        ent_dias = ttk.Entry(calcwrap, textvariable=self.var_calc_dias, width=6)
        ent_dias.grid(row=0, column=3, padx=(4, 0))
        ent_dias.bind("<Return>", lambda e: self._calcular_quebrada())
        ttk.Label(calcwrap, text="Período 2 — Jornada:", font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Entry(calcwrap, textvariable=self.var_calc_jornada2, width=7).grid(row=1, column=1, padx=(4, 12), pady=(4, 0))
        ttk.Label(calcwrap, text="Nº dias (opc.):", font=("Segoe UI", 8)).grid(row=1, column=2, sticky="w", pady=(4, 0))
        ent_dias2 = ttk.Entry(calcwrap, textvariable=self.var_calc_dias2, width=6)
        ent_dias2.grid(row=1, column=3, padx=(4, 0), pady=(4, 0))
        ent_dias2.bind("<Return>", lambda e: self._calcular_quebrada())
        ttk.Button(calcwrap, text="Calcular", command=self._calcular_quebrada).grid(
            row=0, column=4, rowspan=2, padx=(14, 0))
        r += 1
        self.lbl_calc = ttk.Label(f, text="", font=("Segoe UI", 9, "bold"), foreground="#2f7d5b",
                                  justify="left", wraplength=520)
        self.lbl_calc.grid(row=r, column=0, columnspan=4, sticky="w", padx=4, pady=(2, 4))
        r += 1

        ttk.Label(f, text="Carga horária mensal (campo 7):", font=("Segoe UI", 9, "bold")).grid(
            row=r, column=0, columnspan=4, sticky="w", pady=(4, 2))
        r += 1
        self.tabela_frame = ttk.Frame(f)
        self.tabela_frame.grid(row=r, column=0, columnspan=4, sticky=(E, W))

    def _construir_resultado(self, d):
        d.columnconfigure(0, weight=1)
        ttk.Label(d, text="Mapa gerado", font=("Segoe UI", 11, "bold"),
                  foreground="#16334f").grid(sticky="w")
        self.txt_resumo = ttk.Label(d, justify="left", font=("Consolas", 9), anchor="nw")
        self.txt_resumo.grid(sticky=(N, S, E, W), pady=8)

        box = ttk.LabelFrame(d, text="10 · Média da Carga Horária", padding=10)
        box.grid(sticky=(E, W), pady=6)
        for c in range(3):
            box.columnconfigure(c, weight=1)
        self.lbl_media = ttk.Label(box, text="0", font=("Segoe UI", 22, "bold"), foreground="#16334f", anchor="center")
        self.lbl_media.grid(row=0, column=0)
        self.lbl_jornada = ttk.Label(box, text="", font=("Segoe UI", 22, "bold"), foreground="#16334f", anchor="center")
        self.lbl_jornada.grid(row=0, column=1)
        self.lbl_supl = ttk.Label(box, text="", font=("Segoe UI", 22, "bold"), foreground="#16334f", anchor="center")
        self.lbl_supl.grid(row=0, column=2)
        ttk.Label(box, text="Média (Tit./OFA)", font=("Segoe UI", 7), anchor="center").grid(row=1, column=0, sticky=(E, W))
        self.cap_jornada = ttk.Label(box, text="Jornada", font=("Segoe UI", 7), anchor="center")
        self.cap_jornada.grid(row=1, column=1, sticky=(E, W))
        self.cap_supl = ttk.Label(box, text="Carga Suplementar", font=("Segoe UI", 7), anchor="center")
        self.cap_supl.grid(row=1, column=2, sticky=(E, W))

    # -------------------------------------------------------------- tabela
    def _montar_tabela(self):
        for w in self.tabela_frame.winfo_children():
            w.destroy()
        self.cell_vars.clear()
        self.total_ano_labels.clear()

        meses = self._meses_periodo()
        if not meses:
            ttk.Label(self.tabela_frame, text="Informe o mês/ano final (AAAA-MM).").grid()
            return
        anos = anos_do_periodo(meses)
        ativos = {chave(a, m) for a, m in meses}

        # cabeçalho
        ttk.Label(self.tabela_frame, text="Mês", font=("Segoe UI", 8, "bold"),
                  width=11, anchor="w").grid(row=0, column=0, sticky="w")
        for j, a in enumerate(anos):
            ttk.Label(self.tabela_frame, text=str(a), font=("Segoe UI", 8, "bold"),
                      width=7, anchor="center").grid(row=0, column=j + 1)

        for i in range(12):
            ttk.Label(self.tabela_frame, text=MESES[i], font=("Segoe UI", 8),
                      anchor="w").grid(row=i + 1, column=0, sticky="w")
            for j, a in enumerate(anos):
                k = chave(a, i)
                if k in ativos:
                    var = StringVar(value=("" if self.ch.get(k) is None else str(self.ch.get(k))))
                    self.cell_vars[k] = var
                    e = ttk.Entry(self.tabela_frame, textvariable=var, width=7, justify="center")
                    e.grid(row=i + 1, column=j + 1, padx=1, pady=1)
                    var.trace_add("write", lambda *a, kk=k, vv=var: self._on_cell(kk, vv))
                else:
                    ttk.Label(self.tabela_frame, text="—", foreground="#b7bfca",
                              anchor="center", width=7).grid(row=i + 1, column=j + 1)

        ttk.Label(self.tabela_frame, text="Totais", font=("Segoe UI", 8, "bold"),
                  anchor="w").grid(row=13, column=0, sticky="w", pady=(2, 0))
        for j, a in enumerate(anos):
            lbl = ttk.Label(self.tabela_frame, text="0", font=("Segoe UI", 8, "bold"),
                            foreground="#16334f", anchor="center")
            lbl.grid(row=13, column=j + 1, pady=(2, 0))
            self.total_ano_labels[a] = lbl

        self._atualizar_resultado()

    def _on_cell(self, k, var):
        v = var.get().strip().replace(",", ".")
        if v == "":
            self.ch.pop(k, None)
        else:
            try:
                self.ch[k] = float(v)
            except ValueError:
                return
        self._atualizar_resultado()

    # ---------------------------------------------------------- utilitários
    def _meses_periodo(self):
        mf = self.var_mesfinal.get().strip()
        try:
            mes, ano = mf.split("/")
            ano, mes = int(ano), int(mes) - 1
            if not (0 <= mes <= 11):
                return []
        except (ValueError, AttributeError):
            return []
        return periodo_meses(ano, mes, self.var_periodo.get())

    @staticmethod
    def _parcial_quebrada(jornada_str, dias_str):
        """Calcula (jornada / 30) * dias para um período. Retorna None se inválido/vazio."""
        try:
            j = float((jornada_str or "").strip().replace(",", "."))
            d = int(float((dias_str or "").strip().replace(",", ".")))
        except (ValueError, AttributeError):
            return None
        if j <= 0 or d <= 0:
            return None
        if d > 30:
            d = 30
        exato = (j / 30) * d
        return {"j": j, "d": d, "exato": exato, "horas": round(exato)}

    def _calcular_quebrada(self):
        """Calcula a carga horária quebrada de um ou dois períodos e a soma."""
        p1 = self._parcial_quebrada(self.var_calc_jornada.get(), self.var_calc_dias.get())
        p2 = self._parcial_quebrada(self.var_calc_jornada2.get(), self.var_calc_dias2.get())
        if not p1 and not p2:
            self.lbl_calc.configure(
                text="Informe ao menos um período (jornada e nº de dias).", foreground="#8a5a00")
            return

        linhas = []
        if p1:
            linhas.append(f"Período 1: {p1['horas']} h   ({p1['j']:g} ÷ 30 × {p1['d']} = {p1['exato']:.2f})")
        if p2:
            linhas.append(f"Período 2: {p2['horas']} h   ({p2['j']:g} ÷ 30 × {p2['d']} = {p2['exato']:.2f})")
        if p1 and p2:
            total_exato = p1["exato"] + p2["exato"]
            linhas.append(f"► Total: {round(total_exato)} horas   "
                          f"({p1['exato']:.2f} + {p2['exato']:.2f} = {total_exato:.2f})")
        else:
            p = p1 or p2
            linhas.append(f"► {p['horas']} horas")
        self.lbl_calc.configure(text="\n".join(linhas), foreground="#2f7d5b")

    def _on_jornada(self):
        txt = self.cbo_jornada.get()
        for h, n in JORNADAS.items():
            if txt.startswith(n):
                self.var_jornada.set(h)
                break
        self._atualizar_resultado()

    def _on_periodo(self):
        txt = self.cbo_periodo.get()
        for n, desc in PERIODOS.items():
            if desc == txt:
                self.var_periodo.set(n)
                break
        self._montar_tabela()

    def _resultado_atual(self):
        meses = self._meses_periodo()
        if not meses:
            return None
        ano, mes = meses[-1]
        return calcular(
            ch=self.ch, vinculo=self.var_vinculo.get(), jornada=self.var_jornada.get(),
            n_meses=self.var_periodo.get(), mes_final_ano=ano, mes_final_mes=mes,
        )

    def _atualizar_resultado(self, *_):
        res = self._resultado_atual()
        if res is None:
            return
        for a, lbl in self.total_ano_labels.items():
            lbl.configure(text=str(res.totais_anuais.get(a, 0)))

        vinc = "Titular de Cargo" if self.var_vinculo.get() == "titular" else "Ocupante de Função-Atividade (OFA)"
        jn = JORNADAS.get(self.var_jornada.get(), "")
        resumo = (
            f"Nome: {self.var_nome.get()}\n"
            f"RG: {self.var_rg.get()}\n"
            f"CPF: {self.var_cpf.get()}\n"
            f"Cargo: {self.var_cargo.get()}   Faixa/Nível: {self.var_faixa.get()}   DI: {self.var_di.get()}\n"
            f"Vínculo: {vinc}\n"
            f"Jornada atual: {jn} — {self.var_jornada.get()} horas\n"
            f"Período de opção: {res.n_meses} meses\n"
            f"7.A · Total geral: {res.total} horas\n"
            f"Média (7.A ÷ {res.n_meses}): {res.media}"
        )
        self.txt_resumo.configure(text=resumo)

        self.lbl_media.configure(text=str(res.media))
        if res.tipo_quadro == "completo":
            self.lbl_jornada.configure(text=str(res.jornada))
            self.lbl_supl.configure(text=str(res.suplementar))
            self.cap_jornada.configure(text="= Jornada")
            self.cap_supl.configure(text="+ Carga Suplementar")
        else:
            self.lbl_jornada.configure(text="—")
            self.lbl_supl.configure(text="—")
            self.cap_jornada.configure(text="Jornada")
            self.cap_supl.configure(text="Carga Suplementar")

    # --------------------------------------------------------------- ações
    def preencher_todos(self):
        v = self.var_fill.get().strip().replace(",", ".")
        if v == "":
            return
        try:
            val = float(v)
        except ValueError:
            messagebox.showerror(APP_TITULO, "Informe um número válido em horas/mês.")
            return
        for a, m in self._meses_periodo():
            self.ch[chave(a, m)] = val
        self._montar_tabela()

    def novo(self):
        if not messagebox.askyesno(APP_TITULO, "Limpar todos os dados?"):
            return
        self.ch.clear()
        for var, dflt in [
            (self.var_nome, ""), (self.var_rg, ""), (self.var_cpf, ""),
            (self.var_cargo, "PEB"), (self.var_faixa, ""), (self.var_di, ""),
            (self.var_desde, ""), (self.var_doe, ""), (self.var_fill, ""),
        ]:
            var.set(dflt)
        self._set_nomeacao("")
        self.var_vinculo.set("titular")
        self.var_jornada.set(150)
        self.cbo_jornada.set(f"{JORNADAS[150]} — 150 horas")
        self.var_periodo.set(60)
        self.cbo_periodo.set(PERIODOS[60])
        self.var_mesfinal.set(mes_final_padrao())
        self._montar_tabela()

    def _get_nomeacao(self) -> str:
        return self.txt_nomeacao.get("1.0", END).strip()

    def _set_nomeacao(self, texto: str):
        self.txt_nomeacao.delete("1.0", END)
        if texto:
            self.txt_nomeacao.insert("1.0", texto)

    def _coletar_estado(self) -> dict:
        return {
            "nome": self.var_nome.get(), "rg": self.var_rg.get(), "cpf": self.var_cpf.get(),
            "cargo": self.var_cargo.get(), "faixa": self.var_faixa.get(), "di": self.var_di.get(),
            "vinculo": self.var_vinculo.get(), "jornada": self.var_jornada.get(),
            "desde": self.var_desde.get(), "doe": self.var_doe.get(),
            "nomeacao": self._get_nomeacao(),
            "periodo": self.var_periodo.get(), "mes_final": self.var_mesfinal.get(),
            "ch": self.ch,
        }

    def _aplicar_estado(self, d: dict):
        self.var_nome.set(d.get("nome", ""))
        self.var_rg.set(d.get("rg", ""))
        self.var_cpf.set(d.get("cpf", ""))
        self.var_cargo.set(d.get("cargo", "PEB"))
        self.var_faixa.set(d.get("faixa", ""))
        self.var_di.set(d.get("di", ""))
        self.var_vinculo.set(d.get("vinculo", "titular"))
        self.var_jornada.set(int(d.get("jornada", 150)))
        self.cbo_jornada.set(f"{JORNADAS.get(self.var_jornada.get(), 'Jornada Básica')} — {self.var_jornada.get()} horas")
        self.var_desde.set(d.get("desde", ""))
        self.var_doe.set(d.get("doe", ""))
        self._set_nomeacao(d.get("nomeacao", ""))
        self.var_periodo.set(int(d.get("periodo", 60)))
        self.cbo_periodo.set(PERIODOS.get(self.var_periodo.get(), PERIODOS[60]))
        self.var_mesfinal.set(d.get("mes_final", mes_final_padrao()))
        self.ch = {k: float(v) for k, v in d.get("ch", {}).items()}
        self._montar_tabela()

    def salvar(self):
        caminho = filedialog.asksaveasfilename(
            title="Salvar mapa", defaultextension=".mapa.json",
            filetypes=[("Mapa de Carga Horária", "*.json"), ("Todos", "*.*")],
            initialfile=f"mapa_{(self.var_nome.get() or 'docente').split()[0].lower()}.json",
        )
        if not caminho:
            return
        with open(caminho, "w", encoding="utf-8") as fp:
            json.dump(self._coletar_estado(), fp, ensure_ascii=False, indent=2)
        messagebox.showinfo(APP_TITULO, "Mapa salvo com sucesso.")

    def abrir(self):
        caminho = filedialog.askopenfilename(
            title="Abrir mapa", filetypes=[("Mapa de Carga Horária", "*.json"), ("Todos", "*.*")])
        if not caminho:
            return
        try:
            with open(caminho, encoding="utf-8") as fp:
                self._aplicar_estado(json.load(fp))
        except (OSError, ValueError, json.JSONDecodeError) as e:
            messagebox.showerror(APP_TITULO, f"Não foi possível abrir o arquivo:\n{e}")

    def carregar_exemplo(self):
        self.var_nome.set("MARIA DA SILVA SANTOS")
        self.var_rg.set("12.345.678-9")
        self.var_cpf.set("123.456.789-00")
        self.var_cargo.set("PEB II")
        self.var_faixa.set("Faixa 5 / Nível I")
        self.var_di.set("001")
        self.var_vinculo.set("titular")
        self.var_jornada.set(150)
        self.cbo_jornada.set(f"{JORNADAS[150]} — 150 horas")
        self.var_desde.set("01/02/2015")
        self.var_doe.set("05/02/2015")
        self._set_nomeacao("Vice-Diretor de Escola, de 01/02/2016 a 31/12/2018 (DOE 05/02/2016).")
        self.var_periodo.set(60)
        self.cbo_periodo.set(PERIODOS[60])
        self.var_mesfinal.set(mes_final_padrao())
        self.ch = {}
        for i, (a, m) in enumerate(self._meses_periodo()):
            self.ch[chave(a, m)] = 150 + (i % 4) * 10
        self._montar_tabela()

    def exportar_html(self):
        res = self._resultado_atual()
        if res is None:
            messagebox.showerror(APP_TITULO, "Informe o mês/ano final antes de exportar.")
            return
        html = self._gerar_html(res)
        # salva em arquivo temporário e abre no navegador (imprimir -> PDF)
        fd, caminho = tempfile.mkstemp(suffix=".html", prefix="mapa_carga_")
        with os.fdopen(fd, "w", encoding="utf-8") as fp:
            fp.write(html)
        webbrowser.open("file://" + caminho)

    def _dados_export(self, res) -> dict:
        """Reúne os dados atuais do formulário para exportação."""
        return {
            "nome": self.var_nome.get(), "rg": self.var_rg.get(), "cpf": self.var_cpf.get(),
            "cargo": self.var_cargo.get(), "faixa": self.var_faixa.get(), "di": self.var_di.get(),
            "vinculo": self.var_vinculo.get(),
            "jornada": self.var_jornada.get(),
            "jornada_nome": JORNADAS.get(self.var_jornada.get(), ""),
            "desde": self.var_desde.get(), "doe": self.var_doe.get(),
            "nomeacao": self._get_nomeacao(),
            "n_meses": res.n_meses,
            "meses": self._meses_periodo(),
            "ch": self.ch,
            "total": res.total, "media": res.media,
            "tipo_quadro": res.tipo_quadro, "suplementar": res.suplementar,
        }

    def exportar_excel(self):
        res = self._resultado_atual()
        if res is None:
            messagebox.showerror(APP_TITULO, "Informe o mês/ano final antes de exportar.")
            return
        try:
            from excel_export import gerar_mapa_excel
        except ImportError:
            messagebox.showerror(
                APP_TITULO,
                "Biblioteca openpyxl não encontrada. Instale com: pip install openpyxl")
            return
        nome_base = (self.var_nome.get() or "docente").split()[0].lower() if self.var_nome.get() else "docente"
        caminho = filedialog.asksaveasfilename(
            title="Baixar Mapa em Excel", defaultextension=".xlsx",
            filetypes=[("Planilha do Excel", "*.xlsx"), ("Todos", "*.*")],
            initialfile=f"mapa_carga_horaria_{nome_base}.xlsx",
        )
        if not caminho:
            return
        try:
            gerar_mapa_excel(self._dados_export(res), caminho)
        except Exception as e:  # noqa: BLE001
            messagebox.showerror(APP_TITULO, f"Não foi possível gerar o Excel:\n{e}")
            return
        if messagebox.askyesno(APP_TITULO, "Excel gerado com sucesso!\n\nDeseja abrir o arquivo agora?"):
            try:
                if hasattr(os, "startfile"):
                    os.startfile(caminho)  # Windows
                else:
                    webbrowser.open("file://" + caminho)
            except OSError:
                webbrowser.open("file://" + caminho)

    def _gerar_html(self, res) -> str:
        from html import escape
        meses = self._meses_periodo()
        anos = anos_do_periodo(meses)
        ativos = {chave(a, m) for a, m in meses}
        vinc = "Titular de Cargo" if self.var_vinculo.get() == "titular" else "Ocupante de Função-Atividade (OFA)"
        jn = JORNADAS.get(self.var_jornada.get(), "")
        nomeacao = escape(self._get_nomeacao()) or "<span style='color:#8a94a3'>Não há.</span>"

        linhas = ""
        for i in range(12):
            cells = "".join(
                f"<td>{escape(str(int(self.ch[chave(a, i)]))) if chave(a, i) in ativos and chave(a, i) in self.ch else ''}</td>"
                for a in anos
            )
            linhas += f"<tr><td class='l'>{MESES[i]}</td>{cells}</tr>"
        tot_cells = "".join(f"<td>{res.totais_anuais.get(a, 0)}</td>" for a in anos)
        col_anos = "".join(f"<th>{a}</th>" for a in anos)

        if res.tipo_quadro == "completo":
            quadro = (f"<div class='rb'><div><b>{res.media}</b><small>Média (Titular)</small></div>"
                      f"<div><b>{res.jornada}</b><small>= Jornada</small></div>"
                      f"<div><b>{res.suplementar}</b><small>+ Carga Suplementar</small></div></div>")
        else:
            quadro = (f"<div class='rb'><div><b>{res.media}</b><small>Média (Tit./OFA)</small></div>"
                      f"<div><small>Jornada</small></div><div><small>Carga Suplementar</small></div></div>")

        return f"""<!DOCTYPE html><html lang='pt-BR'><head><meta charset='utf-8'>
<title>Mapa de Carga Horária</title><style>
body{{font-family:system-ui,Arial,sans-serif;color:#1f2733;margin:24px;}}
.map{{border:2px solid #000;max-width:800px;margin:auto;}}
.hd{{text-align:center;padding:8px;border-bottom:1.5px solid #000;}}
.hd h3{{margin:0;text-transform:uppercase;}}
.row{{display:grid;border-bottom:1px solid #000;}}
.row:last-child{{border-bottom:none;}}
.c{{padding:6px 8px;border-right:1px solid #000;font-size:13px;}}
.c:last-child{{border-right:none;}}
.c small{{display:block;font-size:9px;text-transform:uppercase;color:#555;}}
.r2{{grid-template-columns:1fr 1fr;}}.r4{{grid-template-columns:repeat(4,1fr);}}.r3{{grid-template-columns:2fr 1fr 1fr;}}
.badge{{background:#1f4e79;color:#fff;padding:6px 8px;font-size:11px;text-transform:uppercase;grid-column:1/-1;}}
table{{border-collapse:collapse;width:100%;font-size:12px;}}
th,td{{border:1px solid #000;padding:3px 5px;text-align:center;}}
td.l{{text-align:left;font-weight:600;}}
tfoot td{{background:#e6f2ec;font-weight:700;}}
.rb{{display:grid;grid-template-columns:repeat(3,1fr);text-align:center;}}
.rb>div{{padding:10px;border-right:1px solid #000;}}.rb>div:last-child{{border-right:none;}}
.rb b{{font-size:26px;display:block;color:#16334f;}}.rb small{{font-size:10px;color:#555;}}
.decl{{padding:8px;font-size:11px;border-top:1px solid #000;color:#333;}}
.sig{{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid #000;}}
.sig>div{{padding:26px 8px 6px;text-align:center;border-right:1px solid #000;font-size:10px;color:#555;}}
.sig>div:last-child{{border-right:none;}}.sig .ln{{border-top:1px solid #000;padding-top:3px;}}
@media print{{@page{{size:A4;margin:12mm;}}.badge{{-webkit-print-color-adjust:exact;print-color-adjust:exact;}}}}
</style></head><body>
<div class='map'>
<div class='hd'><h3>Mapa de Carga Horária</h3><small>ANEXO III · SEDUC / DIPES / DVIF — cálculo de proventos</small></div>
<div class='row r3'><div class='c'><small>1 · Nome</small>{escape(self.var_nome.get()) or '&nbsp;'}</div>
<div class='c'><small>2 · RG</small>{escape(self.var_rg.get()) or '&nbsp;'}</div>
<div class='c'><small>2 · CPF</small>{escape(self.var_cpf.get()) or '&nbsp;'}</div></div>
<div class='row r4'><div class='c'><small>3 · Cargo</small>{escape(self.var_cargo.get()) or '&nbsp;'}</div>
<div class='c'><small>4 · Faixa/Nível</small>{escape(self.var_faixa.get()) or '&nbsp;'}</div>
<div class='c'><small>4 · DI</small>{escape(self.var_di.get()) or '&nbsp;'}</div>
<div class='c'><small>5 · Vínculo</small>{vinc}</div></div>
<div class='row r3'><div class='c'><small>6 · Jornada atual</small>{jn} — {self.var_jornada.get()} horas</div>
<div class='c'><small>6 · Incluído a partir de</small>{escape(self.var_desde.get()) or '&nbsp;'}</div>
<div class='c'><small>6 · DOE</small>{escape(self.var_doe.get()) or '&nbsp;'}</div></div>
<div class='row'><div class='badge'>7 · Carga horária — período de opção: {res.n_meses} meses</div></div>
<div class='row'><div class='c' style='border-right:none'>
<table><thead><tr><th>Mês</th>{col_anos}</tr></thead><tbody>{linhas}
<tr><td class='l'>Totais anuais</td>{tot_cells}</tr></tbody>
<tfoot><tr><td class='l'>7.A · Total geral</td><td colspan='{len(anos)}'>{res.total} horas</td></tr></tfoot></table></div></div>
<div class='row'><div class='badge'>8 · Nomeação/Designação em regime de 40 horas/semanais</div></div>
<div class='row'><div class='c' style='border-right:none;white-space:pre-wrap'>{nomeacao}</div></div>
<div class='row'><div class='badge'>10 · Média (7.A ÷ {res.n_meses} meses, arredondada ao inteiro)</div></div>
<div class='row'><div class='c' style='border-right:none;padding:0'>{quadro}</div></div>
<div class='decl'><b>9 · Declaração:</b> Declaro que estou ciente do nº de aulas constante deste Quadro,
que retrata a minha opção nos termos do Art. 39 (das DDTT) da LC 836/97 ({res.n_meses} meses) para fins de cálculo de proventos.</div>
<div class='sig'><div><div class='ln'>Assinatura do(a) interessado(a)</div></div>
<div><div class='ln'>Assinatura do superior imediato (Diretor da Escola)</div></div></div>
</div></body></html>"""


def main():
    root = Tk()
    root.title(APP_TITULO)
    root.geometry("1100x740")
    root.minsize(920, 600)
    try:
        ttk.Style().theme_use("clam")
    except Exception:
        pass
    MapaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
