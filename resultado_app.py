"""Gerador de resultado para Discord. Python 3, sem dependências externas."""
import json
import re
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont


def load_fonts(root):
    """Register bundled fonts privately, without changing Windows font settings."""
    folder = Path(__file__).parent / 'assets' / 'fonts'
    if sys.platform == 'win32':
        import ctypes
        for file in folder.glob('*.ttf'):
            ctypes.windll.gdi32.AddFontResourceExW(str(file), 0x10, 0)
    families = set(tkfont.families(root))
    sans = next((name for name in ('Inter', 'Inter Variable', 'InterVariable', 'Segoe UI', 'Arial') if name in families), 'TkDefaultFont')
    mono = next((name for name in ('JetBrains Mono', 'Consolas', 'Courier New') if name in families), 'TkFixedFont')
    return sans, mono

DEFAULT_TEMPLATE = """# ╭━━━〔 :crossed_swords: MATCH RESULT 〕━━━╮
# {time1} {placar1} — {placar2} {time2}

# :trophy: WINNER {vencedor}
# :crown: MOTM {motm}
# ━━━━━━━━━━━━━━━━━━

# :first_place: MVP
# 1.{mvp1}  2. {mvp2}
# :dart: MVA
# 1.{mva1}  2. {mva2}
# :shield: MVD
# 1.{mvd1}  2. {mvd2}
# :gloves: GK
# {gk}
━━━━━━━━━━━━━━━━━━

{hms}"""
AWARDS = [('motm', 'MOTM'), ('mvp1', 'MVP 1'), ('mvp2', 'MVP 2'),
          ('mvp3', 'MVP 3'), ('mva1', 'MVA 1'), ('mva2', 'MVA 2'),
          ('mva3', 'MVA 3'), ('mvd1', 'MVD 1'), ('mvd2', 'MVD 2'),
          ('mvd3', 'MVD 3'), ('gk', 'GK 1'), ('gk2', 'GK 2')]
EMOJIS = ('', ':sillyISAGI:', ':sillyRIN:', ':sillyBachira:', ':sillyAiku:',
          ':sillyGagamaru:', ':sillyBarou:', ':sillyReo:', ':sillyKurona:',
          ':sillyKiyora:', ':sillyNagi:', ':sillyRin:', ':sillySae:',
          ':sillyChigiri:', ':sillyKarasu:', ':sillyYukimiya:', ':SillyHiori:',
          ':sillyShidou:', ':sillyKunigami:', ':sillyKAISER:', ':ChibiDon:')

RANKED_TEMPLATE = """# 🏆 RESULTADOS DA {tipo} 🏆

# {time1} X {time2}

# Resultado: {placar1}-{placar2}
# Win: {vencedor}

{refs_linha}
{motm_linha}
# 🏅 MVP: {mvps}
# 🎯 MVA: {mvas}
# 🛡️ MVD: {mvds}
# 🧤 GK: {gks}

# Sets — Melhor de 3
{sets}

# Stats — {time1}
{stats1}

# Stats — {time2}
{stats2}

{hms}
{ping_resultados}"""


def number(raw, label):
    if not re.fullmatch(r'[0-9]+', raw.strip()):
        raise ValueError(label + ': informe um número inteiro de zero ou mais.')
    return int(raw)


def series_result(sets, teams):
    wins = [0, 0]
    lines = []
    gap = False
    for index, item in enumerate(sets, 1):
        a, b = item['a'].strip(), item['b'].strip()
        if not a and not b:
            gap = True
            continue
        if gap:
            raise ValueError('Preencha os sets em ordem, sem pular um set.')
        if max(wins) == 2:
            raise ValueError('A melhor de 3 já terminou. Deixe o set restante vazio.')
        sa, sb = number(a, f'Set {index}, time 1'), number(b, f'Set {index}, time 2')
        if sa == sb:
            raise ValueError(f'Set {index}: informe o placar final sem empate.')
        winner = 0 if sa > sb else 1
        wins[winner] += 1
        line = f'{index}º set: {teams[0]} {sa} — {sb} {teams[1]} | Win: **{teams[winner]}**'
        if item.get('mvp', '').strip():
            line += ' | MVP: **' + item['mvp'].strip() + '**'
        lines.append(line)
    winner = teams[wins.index(2)] if 2 in wins else 'Em andamento'
    return wins, winner, '\n'.join(lines) or 'Nenhum set informado.'


def stats_text(rows):
    lines = []
    for row in rows:
        player = row['player'].strip()
        if not player:
            if any(row.get(k, '').strip() not in ('', '0') for k in ('g', 'a', 'd', 's', 'emoji', 'position')):
                raise ValueError('Selecione o jogador da linha de estatísticas preenchida.')
            continue
        counts = [number(row.get(k, '').strip() or '0', 'Stats ' + player) for k in ('g', 'a', 'd', 's')]
        suffix = ' '.join(filter(None, [row.get('emoji', '').strip(), row.get('position', '').strip()]))
        sub = ' (sub)' if row.get('sub') else ''
        lines.append(f'**{player}{sub}**: {counts[0]}G {counts[1]}A {counts[2]}D {counts[3]}S' + (' ' + suffix if suffix else ''))
    return '\n'.join(lines) or 'Sem estatísticas informadas.'


def generate_extended(values, hms, template, sets, stats):
    wins, winner, set_lines = series_result(sets, [values['time1'], values['time2']])
    values = dict(values, placar1=str(wins[0]), placar2=str(wins[1]))
    base, _ = generate(values, hms, '{motm}')
    data = dict(values, vencedor=winner, tipo=values.get('tipo', 'RANKED'), sets=set_lines,
                stats1=stats_text(stats[0]), stats2=stats_text(stats[1]))
    for prefix, keys in [('mvps', ['mvp1', 'mvp2', 'mvp3']), ('mvas', ['mva1', 'mva2', 'mva3']),
                         ('mvds', ['mvd1', 'mvd2', 'mvd3']), ('gks', ['gk', 'gk2'])]:
        data[prefix] = ', '.join(generate(values, '', '{' + key + '}')[0] for key in keys if values.get(key, '').strip())
    for key, _ in AWARDS:
        data[key] = generate(values, '', '{' + key + '}')[0]
    data['motm_linha'] = '# 👑 MOTM: ' + base if values.get('motm', '').strip() else ''
    data['refs_linha'] = 'REFS: **' + values['refs'] + '**' if values.get('refs', '').strip() else ''
    data['ping_resultados'] = values.get('ping_resultados', '')
    data['hms'] = generate(values, hms, '{hms}')[0]
    return re.sub(r'\{([a-z0-9_]+)\}', lambda m: data.get(m[1], m[0]), template).rstrip(), winner, wins


def generate(values, hms, template):
    scores = []
    for key in ('placar1', 'placar2'):
        raw = values.get(key, '').strip()
        if not re.fullmatch(r'[0-9]+', raw):
            raise ValueError('Preencha os dois placares com números inteiros de zero ou mais.')
        scores.append(int(raw))
    data = {key: values.get(key, '').strip() for key in ('time1', 'time2', 'placar1', 'placar2')}
    data['vencedor'] = ('Empate' if scores[0] == scores[1] else
                        data['time1'] if scores[0] > scores[1] else data['time2'])
    for key, _ in AWARDS:
        data[key] = ' '.join(filter(None, (values.get(key, '').strip(), values.get(key + '_emoji', '').strip())))
    data['hms'] = '\n'.join(line.strip() if line.strip().startswith('-# hm:') else '-# hm: ' + line.strip()
                            for line in hms.splitlines() if line.strip())
    # Substitute known placeholders only; preserve other braces and Discord markup.
    return re.sub(r'\{([a-z0-9_]+)\}', lambda m: data.get(m[1], m[0]), template).rstrip(), data['vencedor']


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.sans, self.mono = load_fonts(self)
        self.title('Resultado da Liga ALSA')
        assets = Path(__file__).parent / 'assets'
        self.window_icon = tk.PhotoImage(file=str(assets / 'icon.png'))
        self.iconphoto(True, self.window_icon)
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ALSA.ResultadoDaLiga')
            self.iconbitmap(str(assets / 'app.ico'))
        self.geometry('1220x840')
        self.minsize(820, 620)
        self.vars = {}
        self.contacts = {'players': {}, 'roles': {}}
        self.pickers = {}
        self.score_widgets = {}
        self.extra_pickers = []
        self.set_rows = []
        self.stat_rows = [[], []]
        self.friendly_scores = ['0', '0']
        self.previous_mode_ranked = False
        self.state_file = Path(os.environ.get('APPDATA', str(Path.home()))) / 'ResultadoDaLiga' / 'preferencias.json'
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        # Import previous portable data once; future updates keep AppData intact.
        legacy = (Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent) / 'preferencias.json'
        if not self.state_file.exists() and legacy.exists():
            self.state_file.write_bytes(legacy.read_bytes())
        self.valid_message = None
        style = ttk.Style(self)
        style.theme_use('clam')
        self.configure(bg='#10131c')
        style.configure('.', background='#10131c', foreground='#e9edf6', font=(self.sans, 10))
        style.configure('TFrame', background='#10131c')
        style.configure('TLabel', background='#10131c', foreground='#e9edf6', font=(self.sans, 10))
        style.configure('TButton', padding=(12, 9), background='#252c40', borderwidth=0)
        style.map('TButton', background=[('active', '#354360')])
        style.configure('Accent.TButton', background='#5865f2', foreground='white', font=(self.sans, 11, 'bold'))
        style.map('Accent.TButton', background=[('active', '#4752c4')])
        style.configure('TEntry', fieldbackground='#1d2333', foreground='#e9edf6', insertcolor='white', padding=6)
        style.configure('TCombobox', fieldbackground='#1d2333', background='#252c40', foreground='#e9edf6', arrowcolor='#b4c3ff', padding=6)
        style.map('TCombobox', fieldbackground=[('readonly', '#1d2333')], foreground=[('readonly', '#e9edf6')])
        style.map('TEntry', fieldbackground=[('readonly', '#202738')], foreground=[('readonly', '#a9b8df')])
        style.configure('TNotebook', background='#10131c', borderwidth=0)
        style.configure('TNotebook.Tab', padding=(14, 10), background='#1d2333', foreground='#aeb8d0')
        style.map('TNotebook.Tab', background=[('selected', '#5865f2')], foreground=[('selected', 'white')])
        style.configure('TLabelframe', background='#10131c', bordercolor='#303950')
        style.configure('TLabelframe.Label', foreground='#a9b8ff', background='#10131c', font=(self.sans, 11, 'bold'))
        style.configure('Treeview', background='#1d2333', fieldbackground='#1d2333', foreground='#e9edf6', rowheight=30)
        style.configure('Treeview.Heading', background='#252c40', foreground='white', padding=7)
        style.map('Treeview', background=[('selected', '#5865f2')])
        self.option_add('*TCombobox*Listbox.background', '#1d2333')
        self.option_add('*TCombobox*Listbox.foreground', '#e9edf6')
        outer = ttk.Frame(self, padding=22)
        outer.pack(fill='both', expand=True)
        header = ttk.Frame(outer)
        header.pack(fill='x', pady=(0, 18))
        self.header_logo = tk.PhotoImage(file=str(assets / 'logo-header.png'))
        ttk.Label(header, image=self.header_logo).pack(side='left', padx=(0, 16))
        heading = ttk.Frame(header)
        heading.pack(side='left', fill='x', expand=True)
        ttk.Label(heading, text='RESULTADO DA LIGA ALSA', font=(self.sans, 24, 'bold')).pack(anchor='w')
        ttk.Label(heading, text='Azure Latch South America League • Da partida ao Discord, em poucos cliques.', foreground='#aeb8d0').pack(anchor='w', pady=(4, 0))
        self.mode_tabs = ttk.Notebook(outer)
        self.mode_tabs.pack(fill='x', pady=(0, 16))
        for name, description in [('Amistoso', 'Placar direto, destaques e HMs. Ideal para amistosos e scrims.'), ('Ranked / Detalhe', 'Melhor de 3, placares dos sets e estatísticas dos dois times.')]:
            page = ttk.Frame(self.mode_tabs, padding=12)
            ttk.Label(page, text=description, foreground='#b5c1df').pack(anchor='w')
            self.mode_tabs.add(page, text=name)
        self.mode_tabs.bind('<<NotebookTabChanged>>', self.change_mode)
        panes = ttk.Panedwindow(outer, orient='horizontal')
        panes.pack(fill='both', expand=True)
        left_container = ttk.Frame(panes)
        input_tabs = ttk.Notebook(left_container)
        self.input_tabs = input_tabs
        input_tabs.pack(fill='both', expand=True)
        left = self.scroll_frame(input_tabs)
        input_tabs.add(left.master.master, text='Partida e prêmios')
        details = self.scroll_frame(input_tabs)
        input_tabs.add(details.master.master, text='Sets e estatísticas')
        self.details_page = details.master.master
        right = ttk.Frame(panes, padding=8)
        panes.add(left_container, weight=1)
        panes.add(right, weight=1)
        left.columnconfigure(1, weight=1)
        left.columnconfigure(2, weight=1)
        for row, (key, label) in enumerate([('time1', 'Time 1 / ping'), ('placar1', 'Placar time 1'), ('time2', 'Time 2 / ping'), ('placar2', 'Placar time 2')]):
            ttk.Label(left, text=label).grid(row=row, column=0, sticky='w', pady=4)
            self.entry(left, key, row, 1, 2, '0' if key.startswith('placar') else '')
        self.winner = tk.StringVar(value='Empate')
        ttk.Label(left, text='Vencedor').grid(row=4, column=0, sticky='w', pady=6)
        ttk.Label(left, textvariable=self.winner).grid(row=4, column=1, columnspan=2, sticky='w')
        ttk.Label(left, text='Jogador / ping').grid(row=5, column=1, sticky='w')
        ttk.Label(left, text='Emoji / personagem').grid(row=5, column=2, sticky='w')
        for row, (key, label) in enumerate(AWARDS, 6):
            ttk.Label(left, text=label).grid(row=row, column=0, sticky='w', pady=4)
            self.entry(left, key, row, 1)
            self.entry(left, key + '_emoji', row, 2)
        hm_row = 6 + len(AWARDS)
        ttk.Label(left, text='HMs — uma por linha').grid(row=hm_row, column=0, columnspan=3, sticky='w', pady=(10, 4))
        self.hms = tk.Text(left, height=5, wrap='word', font=(self.sans, 10), bg='#1d2333', fg='#e9edf6', insertbackground='white', relief='flat', padx=10, pady=10)
        self.hms.grid(row=hm_row + 1, column=0, columnspan=3, sticky='nsew')
        self.hms.bind('<<Modified>>', self.modified)
        self.format_mode = tk.StringVar(value='Template antigo / personalizado')
        self.format_mode.trace_add('write', lambda *_: self.update_preview())
        self.build_details(details)
        tabs = ttk.Notebook(right)
        tabs.pack(fill='both', expand=True)
        preview_tab, template_tab = ttk.Frame(tabs), ttk.Frame(tabs)
        tabs.add(preview_tab, text='Prévia da mensagem')
        tabs.add(template_tab, text='Editar template')
        contacts_tab = ttk.Frame(tabs, padding=8)
        tabs.add(contacts_tab, text='Jogadores e cargos')
        self.build_contacts(contacts_tab)
        self.preview = self.text_area(preview_tab)
        ttk.Label(template_tab, text='Use os marcadores abaixo onde quiser inserir os campos.', wraplength=430).pack(anchor='w', pady=6)
        ttk.Label(template_tab, text='{time1} {placar1} {time2} {placar2} {vencedor}\n{motm} {mvp1} {mvp2} {mva1} {mva2}\n{mvd1} {mvd2} {gk} {hms}', wraplength=430).pack(anchor='w', pady=6)
        self.template = self.text_area(template_tab)
        self.template.insert('1.0', DEFAULT_TEMPLATE)
        self.template.bind('<<Modified>>', self.modified)
        ttk.Button(template_tab, text='Restaurar template inicial', command=self.reset_template).pack(anchor='w', pady=6)
        ttk.Label(template_tab, text='Template Ranked / Scrim: {tipo} {sets} {stats1} {stats2}\n{mvps} {mvas} {mvds} {gks} {refs_linha} {motm_linha}\nTambém aceita os marcadores de times e placares acima.', wraplength=430).pack(anchor='w')
        self.ranked_template = self.text_area(template_tab)
        self.ranked_template.insert('1.0', RANKED_TEMPLATE)
        self.ranked_template.bind('<<Modified>>', self.modified)
        self.status = tk.StringVar()
        ttk.Label(right, textvariable=self.status, wraplength=420).pack(anchor='w', pady=8)
        self.copy_button = ttk.Button(right, text='Copiar mensagem para o Discord', style='Accent.TButton', command=self.copy)
        self.copy_button.pack(fill='x')
        ttk.Button(right, text='Importar cadastros da versão anterior', command=self.import_preferences).pack(fill='x', pady=(8, 0))
        self.load_preferences()
        self.refresh_contacts()
        self.update_preview()
        self.change_mode()
        self.protocol('WM_DELETE_WINDOW', self.close)

    def entry(self, parent, key, row, column, span=1, initial=''):
        var = tk.StringVar(value=initial)
        self.vars[key] = var
        if key.endswith('_emoji'):
            widget = ttk.Combobox(parent, textvariable=var, values=EMOJIS)
        elif key in ('time1', 'time2') or key in dict(AWARDS):
            widget = ttk.Combobox(parent, textvariable=var)
            self.pickers[key] = widget
        else:
            widget = ttk.Entry(parent, textvariable=var)
        widget.grid(row=row, column=column, columnspan=span, sticky='ew', padx=4, pady=4)
        if key in ('placar1', 'placar2'):
            self.score_widgets[key] = widget
        var.trace_add('write', lambda *_: self.update_preview())

    def text_area(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True)
        text = tk.Text(frame, wrap='word', font=(self.mono, 11), undo=True, bg='#171c29', fg='#dbe4fa', insertbackground='white', relief='flat', padx=16, pady=14, selectbackground='#5865f2')
        bar = ttk.Scrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=bar.set)
        bar.pack(side='right', fill='y')
        text.pack(fill='both', expand=True)
        return text

    def scroll_frame(self, parent):
        container = ttk.Frame(parent)
        canvas = tk.Canvas(container, highlightthickness=0, bg='#10131c')
        bar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side='right', fill='y')
        canvas.pack(fill='both', expand=True)
        inner = ttk.Frame(canvas, padding=8)
        item = canvas.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(item, width=event.width))
        def wheel(event):
            canvas.yview_scroll(-int(event.delta / 120), 'units')
        def bind_wheel(widget):
            widget.bind('<MouseWheel>', wheel, add='+')
            for child in widget.winfo_children():
                bind_wheel(child)
        inner.bind('<Map>', lambda _: bind_wheel(inner))
        return inner

    def change_mode(self, _event=None):
        if not hasattr(self, 'copy_button'):
            return
        ranked = self.mode_tabs.index(self.mode_tabs.select()) == 1
        if ranked and not self.previous_mode_ranked:
            self.friendly_scores = [self.vars[k].get() for k in ('placar1', 'placar2')]
        self.previous_mode_ranked = ranked
        self.format_mode.set('Ranked / Scrim (com stats)' if ranked else 'Template antigo / personalizado')
        if ranked:
            self.input_tabs.add(self.details_page, text='Sets e estatísticas')
        else:
            for key, score in zip(('placar1', 'placar2'), self.friendly_scores):
                self.vars[key].set(score)
            self.input_tabs.select(0)
            self.input_tabs.hide(self.details_page)
        self.update_preview()

    def import_preferences(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(title='Escolha o preferencias.json antigo', filetypes=[('Preferências JSON', '*.json')])
        if not filename:
            return
        try:
            data = json.loads(Path(filename).read_text(encoding='utf-8'))
            if not isinstance(data, dict):
                raise ValueError('Arquivo inválido.')
            incoming = {}
            for group in ('players', 'roles'):
                saved = data.get(group, {})
                if not isinstance(saved, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in saved.items()):
                    raise ValueError('Cadastros inválidos.')
                incoming[group] = saved
        except (OSError, ValueError) as error:
            messagebox.showerror('Não foi possível importar', str(error))
            return
        for group in incoming:
            for name, ping in incoming[group].items():
                self.contacts[group].setdefault(name, ping)
        if self.save_preferences():
            self.refresh_contacts()
            self.status.set('Jogadores e cargos importados. Cadastros existentes foram mantidos.')

    def detail_var(self, parent, initial='', kind='text', width=12):
        var = tk.StringVar(value=initial)
        if kind == 'player':
            widget = ttk.Combobox(parent, textvariable=var, width=width)
            self.extra_pickers.append(widget)
        elif kind == 'emoji':
            widget = ttk.Combobox(parent, textvariable=var, values=EMOJIS, width=width)
        else:
            widget = ttk.Entry(parent, textvariable=var, width=width)
        var.trace_add('write', lambda *_: self.update_preview())
        return var, widget

    def build_details(self, parent):
        self.tipo = tk.StringVar(value='RANKED')
        self.refs, widget = self.detail_var(parent)
        ttk.Label(parent, text='REFS (opcional — cole um ou mais pings)').pack(anchor='w')
        widget.pack(fill='x', pady=4)
        self.results_ping, widget = self.detail_var(parent)
        ttk.Label(parent, text='Ping de resultados (opcional)').pack(anchor='w')
        widget.pack(fill='x', pady=4)
        ttk.Label(parent, text='Melhor de 3: primeiro a vencer 2 sets.\nPreencha os gols de cada set; deixe sets não jogados vazios.', wraplength=430).pack(anchor='w', pady=8)
        for index in range(3):
            frame = ttk.LabelFrame(parent, text=f'Set {index + 1}', padding=6)
            frame.pack(fill='x', pady=4)
            row = {}
            for col, (key, label, kind) in enumerate([('a', 'Gols time 1', 'text'), ('b', 'Gols time 2', 'text'), ('mvp', 'MVP opcional', 'player')]):
                ttk.Label(frame, text=label).grid(row=0, column=col, sticky='w')
                row[key], widget = self.detail_var(frame, kind=kind)
                widget.grid(row=1, column=col, sticky='ew', padx=2)
                frame.columnconfigure(col, weight=1)
            self.set_rows.append(row)
        ttk.Label(parent, text='Stats: totais da série por jogador (dos dois times).\nG = gols; A = assistências; D = defesas/desarmes; S = saves.\nInclua reservas com a opção Sub.', wraplength=430).pack(anchor='w', pady=8)
        for team in range(2):
            frame = ttk.LabelFrame(parent, text=f'Estatísticas do time {team + 1}', padding=6)
            frame.pack(fill='x', pady=6)
            ttk.Button(frame, text='+ Adicionar jogador', command=lambda t=team, f=frame: self.add_stat(t, f)).pack(fill='x')
            self.add_stat(team, frame)

    def add_stat(self, team, parent):
        frame = ttk.Frame(parent, padding=(0, 6))
        frame.pack(fill='x')
        row = {}
        row['player'], widget = self.detail_var(frame, kind='player', width=18)
        ttk.Label(frame, text='Jogador').grid(row=0, column=0, sticky='w')
        widget.grid(row=1, column=0, columnspan=2, sticky='ew')
        row['emoji'], widget = self.detail_var(frame, kind='emoji', width=16)
        ttk.Label(frame, text='Personagem / emoji').grid(row=0, column=2, sticky='w')
        widget.grid(row=1, column=2, columnspan=2, sticky='ew')
        for col, key in enumerate(('g', 'a', 'd', 's')):
            ttk.Label(frame, text=key.upper()).grid(row=2, column=col, sticky='w')
            row[key], widget = self.detail_var(frame, '0', width=6)
            widget.grid(row=3, column=col, sticky='ew', padx=2)
            frame.columnconfigure(col, weight=1)
        row['position'], widget = self.detail_var(frame, width=8)
        ttk.Label(frame, text='Posição (CF, WG, GK...)').grid(row=4, column=0, columnspan=2, sticky='w')
        widget.grid(row=5, column=0, columnspan=2, sticky='ew')
        row['sub'] = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame, text='Sub', variable=row['sub'], command=self.update_preview).grid(row=5, column=2)
        self.stat_rows[team].append(row)
        def remove():
            self.stat_rows[team].remove(row)
            self.extra_pickers[:] = [p for p in self.extra_pickers if p.winfo_exists() and not str(p).startswith(str(frame) + '.')]
            frame.destroy()
            self.update_preview()
        ttk.Button(frame, text='Remover', command=remove).grid(row=5, column=3)
        for picker in self.extra_pickers:
            picker.configure(values=sorted(self.contacts['players'], key=str.casefold))

    def modified(self, event):
        if event.widget.edit_modified():
            event.widget.edit_modified(False)
            self.update_preview()

    def update_preview(self):
        if not hasattr(self, 'copy_button'):
            return
        try:
            extended = self.format_mode.get() == 'Ranked / Scrim (com stats)'
            for widget in self.score_widgets.values():
                widget.configure(state='readonly' if extended else 'normal')
            values = {k: v.get() for k, v in self.vars.items()}
            for key in self.pickers:
                group = 'roles' if key in ('time1', 'time2') else 'players'
                values[key] = self.contacts[group].get(values[key], values[key])
            if extended:
                resolve = lambda text: self.contacts['players'].get(text, text)
                sets = [{k: resolve(v.get()) if k == 'mvp' else v.get() for k, v in row.items()} for row in self.set_rows]
                stats = [[{k: resolve(v.get()) if k == 'player' else v.get() for k, v in row.items()} for row in rows] for rows in self.stat_rows]
                values.update(tipo=self.tipo.get(), refs=self.refs.get(), ping_resultados=self.results_ping.get())
                message, winner, wins = generate_extended(values, self.hms.get('1.0', 'end-1c'), self.ranked_template.get('1.0', 'end-1c'), sets, stats)
                # Show the series score in the main form, derived from sets.
                for key, score in zip(('placar1', 'placar2'), wins):
                    if self.vars[key].get() != str(score):
                        self.vars[key].set(str(score))
            else:
                message, winner = generate(values, self.hms.get('1.0', 'end-1c'), self.template.get('1.0', 'end-1c'))
            self.valid_message = message
            self.winner.set(winner or 'Preencha o nome do time vencedor')
            self.status.set(f'{len(message)} caracteres. ' + ('Mensagem longa: talvez seja necessário enviar em partes no Discord.' if len(message) > 2000 else 'Pronta para copiar.'))
            self.copy_button.configure(state='normal' if message else 'disabled')
        except ValueError as error:
            self.valid_message = None
            message = str(error)
            self.winner.set('—')
            self.status.set(message)
            self.copy_button.configure(state='disabled')
        self.preview.configure(state='normal')
        self.preview.delete('1.0', 'end')
        self.preview.insert('1.0', message)
        self.preview.configure(state='disabled')

    def copy(self):
        if self.valid_message:
            try:
                self.clipboard_clear()
                self.clipboard_append(self.valid_message)
                self.update()
                self.status.set('Mensagem copiada! Cole no Discord com Ctrl+V.')
            except tk.TclError:
                messagebox.showerror('Não foi possível copiar', 'Tente novamente em alguns segundos.')

    def reset_template(self):
        self.template.delete('1.0', 'end')
        self.template.insert('1.0', DEFAULT_TEMPLATE)
        self.update_preview()

    def load_preferences(self):
        try:
            data = json.loads(self.state_file.read_text(encoding='utf-8'))
            for group in self.contacts:
                saved = data.get(group, {})
                if isinstance(saved, dict):
                    self.contacts[group] = {k: v for k, v in saved.items() if isinstance(k, str) and isinstance(v, str)}
            if isinstance(data.get('template'), str):
                self.template.delete('1.0', 'end')
                self.template.insert('1.0', data['template'])
            if isinstance(data.get('ranked_template'), str):
                self.ranked_template.delete('1.0', 'end')
                self.ranked_template.insert('1.0', data['ranked_template'])
        except (OSError, ValueError, AttributeError):
            pass

    def build_contacts(self, parent):
        ttk.Label(parent, text='Cadastre uma vez e selecione pelo nome nos campos da partida.', wraplength=400).pack(anchor='w', pady=6)
        self.contact_kind = tk.StringVar(value='Jogador')
        ttk.Combobox(parent, textvariable=self.contact_kind, values=('Jogador', 'Cargo / time'), state='readonly').pack(fill='x', pady=4)
        ttk.Label(parent, text='Nome para reconhecer (ex.: Vielism ou Requiem)').pack(anchor='w')
        self.contact_name = tk.StringVar()
        ttk.Entry(parent, textvariable=self.contact_name).pack(fill='x', pady=4)
        ttk.Label(parent, text='ID ou ping (ex.: 123456789 ou <@123456789>)').pack(anchor='w')
        self.contact_ping = tk.StringVar()
        ttk.Entry(parent, textvariable=self.contact_ping).pack(fill='x', pady=4)
        ttk.Button(parent, text='Salvar / atualizar', command=self.save_contact).pack(fill='x', pady=6)
        self.contact_list = ttk.Treeview(parent, columns=('kind', 'name', 'ping'), show='headings', selectmode='browse', height=8)
        for col, label, width in [('kind', 'Tipo', 70), ('name', 'Nome', 110), ('ping', 'Ping', 170)]:
            self.contact_list.heading(col, text=label)
            self.contact_list.column(col, width=width)
        self.contact_list.pack(fill='both', expand=True)
        self.contact_list.bind('<<TreeviewSelect>>', self.select_contact)
        ttk.Button(parent, text='Excluir selecionado', command=self.delete_contact).pack(fill='x', pady=6)

    def refresh_contacts(self):
        self.contact_list.delete(*self.contact_list.get_children())
        for group, label in [('players', 'Jogador'), ('roles', 'Cargo / time')]:
            for name, ping in sorted(self.contacts[group].items(), key=lambda item: item[0].casefold()):
                self.contact_list.insert('', 'end', values=(label, name, ping))
        for key, widget in self.pickers.items():
            group = 'roles' if key in ('time1', 'time2') else 'players'
            widget.configure(values=sorted(self.contacts[group], key=str.casefold))
        for widget in self.extra_pickers:
            widget.configure(values=sorted(self.contacts['players'], key=str.casefold))
        self.update_preview()

    def select_contact(self, _event):
        selected = self.contact_list.selection()
        if selected:
            kind, name, ping = self.contact_list.item(selected[0], 'values')
            self.contact_kind.set(kind)
            self.contact_name.set(name)
            self.contact_ping.set(ping)

    def save_contact(self):
        name = self.contact_name.get().strip()
        raw = self.contact_ping.get().strip()
        group = 'players' if self.contact_kind.get() == 'Jogador' else 'roles'
        pattern = r'<@!?(\d+)>' if group == 'players' else r'<@&(\d+)>'
        match = re.fullmatch(pattern, raw)
        identifier = raw if re.fullmatch(r'[0-9]+', raw) else match[1] if match else None
        if not name or not identifier:
            messagebox.showerror('Confira o cadastro', 'Preencha o nome e cole o ID numérico ou o ping correto. Jogador: <@ID>. Cargo: <@&ID>.')
            return
        ping = ('<@' if group == 'players' else '<@&') + identifier + '>'
        previous = self.contacts[group].get(name)
        self.contacts[group][name] = ping
        if not self.save_preferences():
            if previous is None:
                del self.contacts[group][name]
            else:
                self.contacts[group][name] = previous
            return
        self.refresh_contacts()
        self.status.set('Cadastro salvo! Selecione o nome no campo da partida.')

    def delete_contact(self):
        selected = self.contact_list.selection()
        if not selected:
            return
        kind, name, ping = self.contact_list.item(selected[0], 'values')
        group = 'players' if kind == 'Jogador' else 'roles'
        del self.contacts[group][name]
        if not self.save_preferences():
            self.contacts[group][name] = ping
            return
        for key in self.pickers:
            expected = 'roles' if key in ('time1', 'time2') else 'players'
            if expected == group and self.vars[key].get() == name:
                self.vars[key].set(ping)
        if group == 'players':
            for row in self.set_rows:
                if row['mvp'].get() == name:
                    row['mvp'].set(ping)
            for rows in self.stat_rows:
                for row in rows:
                    if row['player'].get() == name:
                        row['player'].set(ping)
        self.refresh_contacts()

    def save_preferences(self):
        try:
            data = {'template': self.template.get('1.0', 'end-1c'), **self.contacts}
            if hasattr(self, 'ranked_template'):
                data['ranked_template'] = self.ranked_template.get('1.0', 'end-1c')
            temporary = self.state_file.with_suffix('.tmp')
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(self.state_file)
        except OSError:
            messagebox.showwarning('Não foi possível salvar', 'Não foi possível salvar nesta pasta. Verifique se ela permite gravar arquivos.')
            return False
        return True

    def close(self):
        if self.save_preferences():
            self.destroy()


if __name__ == '__main__':
    App().mainloop()

