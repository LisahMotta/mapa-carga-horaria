/* ============================================================
   Mapa de Carga Horária — Cálculo de Proventos (Aposentadoria)
   ANEXO III — SEDUC / CGRH / URE São José dos Campos
   Lógica de cálculo baseada na LC 836/97 (Art. 39 DDTT).
   ============================================================ */

'use strict';

const STORAGE_KEY = 'mapa-carga-horaria/v1';

const MESES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
];

const JORNADAS = {
  96: 'Jornada Reduzida',
  120: 'Jornada Inicial',
  150: 'Jornada Básica',
  200: 'Jornada Completa'
};

/* Carreiras e jornadas, com a tabela a que cada jornada pertence. */
const CARREIRAS = {
  antiga: {
    rotulo: 'Antiga carreira',
    jornadas: [
      { tabela: 1, nome: 'Integral', horas: 200 },
      { tabela: 2, nome: 'Básica', horas: 150 },
      { tabela: 3, nome: 'Inicial', horas: 120 },
      { tabela: 4, nome: 'Reduzida', horas: 96 }
    ]
  },
  nova: {
    rotulo: 'Nova carreira',
    jornadas: [
      { tabela: 1, nome: 'Ampliada', horas: 200 },
      { tabela: 2, nome: 'Completa', horas: 125 }
    ]
  }
};

function infoJornada(carreira, tabela) {
  const list = (CARREIRAS[carreira] || CARREIRAS.antiga).jornadas;
  return list.find((j) => j.tabela === Number(tabela)) || list[0];
}

/* Estado da aplicação. ch: mapa "YYYY-MM" -> horas (número). */
const state = {
  nome: '', rg: '', cpf: '', cargo: 'PEB', faixa: '', di: '',
  vinculo: 'titular',
  carreira: 'antiga',
  jornadaTabela: 2,
  jornada: 150,
  jornadaNome: 'Básica',
  jornadaDesde: '', doe: '',
  nomeacao: '',
  periodo: 60,
  mesFinal: '',
  ch: {}
};

/* Recalcula jornada (horas) e nome a partir de carreira + tabela. */
function aplicarJornada() {
  const info = infoJornada(state.carreira, state.jornadaTabela);
  state.jornada = info.horas;
  state.jornadaNome = info.nome;
  state.jornadaTabela = info.tabela;
}

/* Preenche o <select id="jornada"> conforme a carreira selecionada. */
function popularJornadas() {
  const sel = document.querySelector('#jornada');
  if (!sel) return;
  const list = (CARREIRAS[state.carreira] || CARREIRAS.antiga).jornadas;
  sel.innerHTML = list.map((j) =>
    `<option value="${j.tabela}">Tabela ${j.tabela} — Jornada ${j.nome} — ${j.horas} horas</option>`).join('');
  sel.value = String(state.jornadaTabela);
}

/* ---------- utilidades ---------- */
const $ = (sel) => document.querySelector(sel);
const key = (ano, mes) => `${ano}-${String(mes + 1).padStart(2, '0')}`; // mes 0-based

function defaultMesFinal() {
  const d = new Date();
  // mês anterior ao atual como padrão razoável
  d.setDate(1);
  d.setMonth(d.getMonth() - 1);
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`; // MM/AAAA
}

/* Retorna a lista de {ano, mes(0-based)} dos `periodo` meses que terminam em mesFinal (MM/AAAA). */
function periodoMeses() {
  const out = [];
  if (!state.mesFinal) return out;
  const [am, ay] = state.mesFinal.split('/').map(Number);
  if (!ay || !am || am < 1 || am > 12) return out;
  let y = ay, m = am - 1; // 0-based
  for (let i = 0; i < state.periodo; i++) {
    out.push({ ano: y, mes: m });
    m--;
    if (m < 0) { m = 11; y--; }
  }
  return out.reverse(); // do mais antigo ao mais recente
}

/* ---------- cálculo ---------- */
function calcular() {
  const meses = periodoMeses();
  const ativos = new Set(meses.map((x) => key(x.ano, x.mes)));

  let total = 0;
  ativos.forEach((k) => { total += Number(state.ch[k]) || 0; });

  const nMeses = state.periodo;
  const media = nMeses > 0 ? Math.round(total / nMeses) : 0;
  const jornada = Number(state.jornada);

  let quadro; // como preencher o campo 10
  if (state.vinculo === 'ofa') {
    // OFA: preencher somente o 1º quadro (média)
    quadro = { tipo: 'unico', media };
  } else if (media < jornada) {
    // Titular com média < jornada: preencher apenas o 1º quadro
    quadro = { tipo: 'unico', media };
  } else {
    quadro = { tipo: 'completo', media, jornada, suplementar: media - jornada };
  }

  return { meses, ativos, total, nMeses, media, jornada, quadro };
}

/* ---------- tabela de entrada (colunas = anos) ---------- */
function anosDoPeriodo(meses) {
  const anos = [...new Set(meses.map((x) => x.ano))].sort((a, b) => a - b);
  return anos;
}

function renderEntrada() {
  const wrap = $('#tabela-entrada');
  const meses = periodoMeses();
  if (meses.length === 0) {
    wrap.innerHTML = '<p class="hint">Informe o mês/ano final do período para gerar a tabela.</p>';
    return;
  }
  const anos = anosDoPeriodo(meses);
  const ativos = new Set(meses.map((x) => key(x.ano, x.mes)));

  let html = '<table class="entry"><thead><tr><th>Mês</th>';
  anos.forEach((a) => { html += `<th>${a}</th>`; });
  html += '</tr></thead><tbody>';

  for (let m = 0; m < 12; m++) {
    html += `<tr><td class="month-label">${MESES[m]}</td>`;
    anos.forEach((a) => {
      const k = key(a, m);
      const on = ativos.has(k);
      const val = state.ch[k] != null ? state.ch[k] : '';
      html += `<td class="${on ? '' : 'off'}">` +
        `<input type="number" min="0" step="1" data-k="${k}" ` +
        `value="${on ? val : ''}" ${on ? '' : 'disabled'} /></td>`;
    });
    html += '</tr>';
  }

  // totais anuais
  html += '<tr class="total-row"><td class="month-label">Totais anuais</td>';
  anos.forEach((a) => {
    let t = 0;
    for (let m = 0; m < 12; m++) {
      const k = key(a, m);
      if (ativos.has(k)) t += Number(state.ch[k]) || 0;
    }
    html += `<td data-total-ano="${a}">${t || ''}</td>`;
  });
  html += '</tr>';

  html += '</tbody></table>';
  wrap.innerHTML = html;

  wrap.querySelectorAll('input[data-k]').forEach((inp) => {
    inp.addEventListener('input', (e) => {
      const k = e.target.dataset.k;
      const v = e.target.value;
      if (v === '') delete state.ch[k];
      else state.ch[k] = Number(v);
      atualizarTotaisAnuais();
      renderMapa();
      salvar();
    });
  });
}

function atualizarTotaisAnuais() {
  const meses = periodoMeses();
  const ativos = new Set(meses.map((x) => key(x.ano, x.mes)));
  anosDoPeriodo(meses).forEach((a) => {
    let t = 0;
    for (let m = 0; m < 12; m++) {
      const k = key(a, m);
      if (ativos.has(k)) t += Number(state.ch[k]) || 0;
    }
    const cell = document.querySelector(`[data-total-ano="${a}"]`);
    if (cell) cell.textContent = t || '';
  });
}

/* ---------- render do mapa (saída) ---------- */
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}

function renderMapa() {
  const r = calcular();
  const vinc = state.vinculo === 'titular' ? 'Titular de Cargo' : 'Ocupante de Função-Atividade (OFA)';

  const anos = anosDoPeriodo(r.meses);
  const ativos = r.ativos;

  // Tabela de carga horária (linhas = meses, colunas = anos)
  let chTable = '<table class="mapa__ch-table"><thead><tr><th>Mês</th>';
  anos.forEach((a) => { chTable += `<th>${a}</th>`; });
  chTable += '</tr></thead><tbody>';
  for (let m = 0; m < 12; m++) {
    chTable += `<tr><td class="mlabel">${MESES[m]}</td>`;
    anos.forEach((a) => {
      const k = key(a, m);
      chTable += `<td>${ativos.has(k) && state.ch[k] != null ? esc(state.ch[k]) : ''}</td>`;
    });
    chTable += '</tr>';
  }
  chTable += '<tr><td class="mlabel">Totais anuais</td>';
  anos.forEach((a) => {
    let t = 0;
    for (let m = 0; m < 12; m++) { const k = key(a, m); if (ativos.has(k)) t += Number(state.ch[k]) || 0; }
    chTable += `<td>${t || ''}</td>`;
  });
  chTable += '</tr></tbody>';
  chTable += `<tfoot><tr><td class="mlabel">7.A · Total geral</td><td colspan="${anos.length}">${r.total} horas</td></tr></tfoot>`;
  chTable += '</table>';

  // Campo 10 — resultado
  let resultado;
  if (r.quadro.tipo === 'unico') {
    resultado = `
      <div class="result-box">
        <div><div class="big">${r.quadro.media}</div><div class="cap">Média Carga Horária<br>Titular de Cargo / OFA</div></div>
        <div><div class="cap">Jornada</div></div>
        <div><div class="cap">Carga Suplementar</div></div>
      </div>`;
  } else {
    resultado = `
      <div class="result-box">
        <div><div class="big">${r.quadro.media}</div><div class="cap">Média Carga Horária<br>Titular de Cargo</div></div>
        <div><div class="big">${r.quadro.jornada}</div><div class="op">=</div><div class="cap">Jornada</div></div>
        <div><div class="big">${r.quadro.suplementar}</div><div class="op">+</div><div class="cap">Carga Suplementar</div></div>
      </div>`;
  }

  const html = `
    <div class="mapa__head">
      <h3>Mapa de Carga Horária</h3>
      <small>Quadro da carga horária para cálculo de proventos — ANEXO III · SEDUC / CGRH / URE São José dos Campos</small>
    </div>

    <div class="mapa__row r-3">
      <div class="mapa__cell"><span class="lbl">1 · Nome</span><span class="val">${esc(state.nome) || '&nbsp;'}</span></div>
      <div class="mapa__cell"><span class="lbl">2 · RG</span><span class="val">${esc(state.rg) || '&nbsp;'}</span></div>
      <div class="mapa__cell"><span class="lbl">2 · CPF</span><span class="val">${esc(state.cpf) || '&nbsp;'}</span></div>
    </div>
    <div class="mapa__row r-4">
      <div class="mapa__cell"><span class="lbl">3 · Cargo/Função</span><span class="val">${esc(state.cargo) || '&nbsp;'}</span></div>
      <div class="mapa__cell"><span class="lbl">4 · Faixa/Nível</span><span class="val">${esc(state.faixa) || '&nbsp;'}</span></div>
      <div class="mapa__cell"><span class="lbl">4 · DI</span><span class="val">${esc(state.di) || '&nbsp;'}</span></div>
      <div class="mapa__cell"><span class="lbl">5 · Vínculo</span><span class="val">${vinc}</span></div>
    </div>
    <div class="mapa__row r-3">
      <div class="mapa__cell"><span class="lbl">6 · Jornada atual</span><span class="val">Jornada ${esc(state.jornadaNome)} — Tabela ${state.jornadaTabela} — ${state.jornada} horas</span></div>
      <div class="mapa__cell"><span class="lbl">6 · Incluído a partir de</span><span class="val">${esc(state.jornadaDesde) || '&nbsp;'}</span></div>
      <div class="mapa__cell"><span class="lbl">6 · DOE</span><span class="val">${esc(state.doe) || '&nbsp;'}</span></div>
    </div>

    <div class="mapa__row"><div class="mapa__badge">7 · Carga horária — período de opção: ${r.nMeses} meses</div></div>
    <div class="mapa__row"><div class="mapa__cell" style="border-right:none">${chTable}</div></div>

    <div class="mapa__row"><div class="mapa__badge">8 · Nomeação/Designação em regime de 40 horas/semanais</div></div>
    <div class="mapa__row"><div class="mapa__cell" style="border-right:none;white-space:pre-wrap">${esc(state.nomeacao).trim() || '<span style="color:#8a94a3">Não há.</span>'}</div></div>

    <div class="mapa__row"><div class="mapa__badge">10 · Média da carga horária (7.A ÷ ${r.nMeses} meses, arredondada ao inteiro)</div></div>
    <div class="mapa__row"><div class="mapa__cell" style="border-right:none;padding:0">${resultado}</div></div>

    <div class="decl">
      <strong>9 · Declaração:</strong> Declaro que estou ciente do nº de aulas constante deste Quadro, que
      retrata a minha opção nos termos do Art. 39 (das DDTT) da LC 836/97 (${r.nMeses} meses) para fins de
      cálculo de proventos.
    </div>
    <div class="signatures">
      <div><div class="line">Assinatura do(a) interessado(a)</div></div>
      <div><div class="line">Assinatura do superior imediato (Diretor da Escola)</div></div>
    </div>
    <div class="note-obs">
      Mapa de Carga Horária elaborado de acordo com o PA SPPREV nº 756/2015 e Informação UCRH nº 246/2016.
      Verificar sempre a SED para evitar divergências. Homologação: URE São José dos Campos.
    </div>
  `;

  $('#mapa').innerHTML = html;
}

/* ---------- persistência ---------- */
function salvar() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) { /* ignore */ }
}
function carregar() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return false;
    Object.assign(state, JSON.parse(raw));
    migrarFormatoDatas();
    reconciliarJornada();
    return true;
  } catch (e) { return false; }
}

/* Ajusta carreira/tabela de dados salvos antigos (que só tinham jornada em horas). */
function reconciliarJornada() {
  if (!state.carreira) state.carreira = 'antiga';
  const list = (CARREIRAS[state.carreira] || CARREIRAS.antiga).jornadas;
  const byTab = list.find((j) => j.tabela === Number(state.jornadaTabela));
  if (byTab && byTab.horas === Number(state.jornada)) return; // já consistente
  const byHoras = list.find((j) => j.horas === Number(state.jornada));
  if (byHoras) state.jornadaTabela = byHoras.tabela;
}

/* Converte dados salvos no formato antigo (ISO) para DD/MM/AAAA e MM/AAAA. */
function migrarFormatoDatas() {
  const isoDia = (s) => /^\d{4}-\d{2}-\d{2}$/.test(s || '');
  const isoMes = (s) => /^\d{4}-\d{2}$/.test(s || '');
  if (isoDia(state.jornadaDesde)) { const [y, m, d] = state.jornadaDesde.split('-'); state.jornadaDesde = `${d}/${m}/${y}`; }
  if (isoDia(state.doe)) { const [y, m, d] = state.doe.split('-'); state.doe = `${d}/${m}/${y}`; }
  if (isoMes(state.mesFinal)) { const [y, m] = state.mesFinal.split('-'); state.mesFinal = `${m}/${y}`; }
}

/* ---------- vincular controles ---------- */
function bindForm() {
  const map = {
    '#nome': 'nome', '#rg': 'rg', '#cpf': 'cpf', '#cargo': 'cargo',
    '#faixa': 'faixa', '#di': 'di', '#jornada-desde': 'jornadaDesde', '#doe': 'doe',
    '#nomeacao': 'nomeacao'
  };
  Object.entries(map).forEach(([sel, prop]) => {
    const el = $(sel);
    el.value = state[prop] || '';
    el.addEventListener('input', () => { state[prop] = el.value; renderMapa(); salvar(); });
  });

  document.querySelectorAll('input[name="vinculo"]').forEach((r) => {
    r.checked = r.value === state.vinculo;
    r.addEventListener('change', () => {
      if (r.checked) { state.vinculo = r.value; renderMapa(); salvar(); }
    });
  });

  const selCarreira = $('#carreira');
  const selJornada = $('#jornada');
  selCarreira.value = state.carreira;
  popularJornadas();
  selCarreira.addEventListener('change', () => {
    state.carreira = selCarreira.value;
    state.jornadaTabela = (CARREIRAS[state.carreira] || CARREIRAS.antiga).jornadas[0].tabela;
    aplicarJornada();
    popularJornadas();
    renderMapa(); salvar();
  });
  selJornada.addEventListener('change', () => {
    state.jornadaTabela = Number(selJornada.value);
    aplicarJornada();
    renderMapa(); salvar();
  });

  const selPeriodo = $('#periodo');
  selPeriodo.value = String(state.periodo);
  selPeriodo.addEventListener('change', () => {
    state.periodo = Number(selPeriodo.value);
    renderEntrada(); renderMapa(); salvar();
  });

  const mesFinal = $('#mes-final');
  mesFinal.value = state.mesFinal || '';
  mesFinal.addEventListener('change', () => {
    state.mesFinal = mesFinal.value;
    renderEntrada(); renderMapa(); salvar();
  });

  $('#btn-fill').addEventListener('click', () => {
    const v = $('#fill-valor').value;
    if (v === '') return;
    periodoMeses().forEach((x) => { state.ch[key(x.ano, x.mes)] = Number(v); });
    renderEntrada(); renderMapa(); salvar();
  });

  $('#btn-imprimir').addEventListener('click', () => window.print());
  $('#btn-limpar').addEventListener('click', limpar);
  $('#btn-exemplo').addEventListener('click', carregarExemplo);
}

/* ---------- Calculadora: carga horária quebrada no mês ---------- */
function bindCalculadora() {
  const j1 = $('#calc-jornada1'), d1 = $('#calc-dias1');
  const j2 = $('#calc-jornada2'), d2 = $('#calc-dias2');
  const out = $('#calc-resultado');
  j1.value = state.jornada; // pré-preenche com a jornada selecionada

  // Calcula um período: (jornada / 30) * dias. Retorna null se inválido/vazio.
  const parcial = (jVal, dVal) => {
    const j = Number(jVal) || 0;
    let d = Math.floor(Number(dVal) || 0);
    if (j <= 0 || d <= 0) return null;
    if (d > 30) d = 30;
    const exato = (j / 30) * d;
    return { j, d, exato, horas: Math.round(exato) };
  };

  const linha = (n, p) =>
    `<div class="calc-line">Período ${n}: <b>${p.horas}</b> h ` +
    `<small>( ${p.j} ÷ 30 × ${p.d} = ${p.exato.toFixed(2)} )</small></div>`;

  const calc = () => {
    const p1 = parcial(j1.value, d1.value);
    const p2 = parcial(j2.value, d2.value);
    if (!p1 && !p2) {
      out.innerHTML = '<span style="color:#8a94a3">Informe ao menos um período (jornada e nº de dias).</span>';
      return;
    }
    let html = '';
    if (p1) html += linha(1, p1);
    if (p2) html += linha(2, p2);
    if (p1 && p2) {
      const totalExato = p1.exato + p2.exato;
      const total = Math.round(totalExato);
      html += `<div class="calc-total">Total: <span class="num">${total}</span> horas ` +
        `<small>&nbsp;( ${p1.exato.toFixed(2)} + ${p2.exato.toFixed(2)} = ${totalExato.toFixed(2)} )</small></div>`;
    } else {
      const p = p1 || p2;
      html += `<div class="calc-total"><span class="num">${p.horas}</span> horas</div>`;
    }
    out.innerHTML = html;
  };

  $('#btn-calcular').addEventListener('click', calc);
  [j1, d1, j2, d2].forEach((el) => el.addEventListener('keydown', (e) => { if (e.key === 'Enter') calc(); }));
}

/* ---------- Calculadora: Jornada + Carga Suplementar (por mês) ---------- */
function bindCalculadoraSuplementar() {
  const bJ = $('#calc2-jornada'), bA = $('#calc2-aulas'), out = $('#calc2-resultado');
  bJ.value = state.jornada; // pré-preenche com a jornada selecionada

  const calc = () => {
    const j = Number(bJ.value) || 0;
    const a = Number(bA.value) || 0;
    if (j <= 0 && a <= 0) {
      out.innerHTML = '<span style="color:#8a94a3">Informe a jornada e/ou o nº de aulas.</span>';
      return;
    }
    const supl = a * 5;
    const total = j + supl;
    out.innerHTML =
      `<div class="calc-line">Carga suplementar: <b>${supl}</b> h <small>( ${a} × 5 )</small></div>` +
      `<div class="calc-total">Total do mês: <span class="num">${total}</span> horas ` +
      `<small>&nbsp;( ${j} + ${supl} )</small></div>`;
  };

  $('#btn-calcular2').addEventListener('click', calc);
  [bJ, bA].forEach((el) => el.addEventListener('keydown', (e) => { if (e.key === 'Enter') calc(); }));
}

function limpar() {
  if (!confirm('Limpar todos os dados do mapa?')) return;
  localStorage.removeItem(STORAGE_KEY);
  Object.assign(state, {
    nome: '', rg: '', cpf: '', cargo: 'PEB', faixa: '', di: '',
    vinculo: 'titular', carreira: 'antiga', jornadaTabela: 2, jornada: 150, jornadaNome: 'Básica',
    jornadaDesde: '', doe: '', nomeacao: '',
    periodo: 60, mesFinal: defaultMesFinal(), ch: {}
  });
  sincronizarForm();
  renderEntrada(); renderMapa(); salvar();
}

function carregarExemplo() {
  Object.assign(state, {
    nome: 'MARIA DA SILVA SANTOS',
    rg: '12.345.678-9', cpf: '123.456.789-00',
    cargo: 'PEB II', faixa: 'Faixa 5 / Nível I', di: '001',
    vinculo: 'titular', carreira: 'antiga', jornadaTabela: 2, jornada: 150, jornadaNome: 'Básica',
    jornadaDesde: '01/02/2015', doe: '05/02/2015',
    nomeacao: 'Vice-Diretor de Escola, de 01/02/2016 a 31/12/2018 (DOE 05/02/2016).',
    periodo: 60, mesFinal: defaultMesFinal(), ch: {}
  });
  // preenche 60 meses variando entre 150 e 180 horas
  periodoMeses().forEach((x, i) => {
    state.ch[key(x.ano, x.mes)] = 150 + (i % 4) * 10; // 150,160,170,180...
  });
  sincronizarForm();
  renderEntrada(); renderMapa(); salvar();
}

/* Reaplica valores do state nos controles do formulário. */
function sincronizarForm() {
  $('#nome').value = state.nome; $('#rg').value = state.rg; $('#cpf').value = state.cpf;
  $('#cargo').value = state.cargo; $('#faixa').value = state.faixa; $('#di').value = state.di;
  $('#jornada-desde').value = state.jornadaDesde; $('#doe').value = state.doe;
  $('#nomeacao').value = state.nomeacao || '';
  aplicarJornada();
  $('#carreira').value = state.carreira;
  popularJornadas();
  $('#periodo').value = String(state.periodo);
  $('#mes-final').value = state.mesFinal;
  document.querySelectorAll('input[name="vinculo"]').forEach((r) => { r.checked = r.value === state.vinculo; });
}

/* ---------- init ---------- */
function init() {
  if (!carregar()) {
    state.mesFinal = defaultMesFinal();
  } else if (!state.mesFinal) {
    state.mesFinal = defaultMesFinal();
  }
  bindForm();
  bindCalculadora();
  bindCalculadoraSuplementar();
  sincronizarForm();
  renderEntrada();
  renderMapa();
}

document.addEventListener('DOMContentLoaded', init);
