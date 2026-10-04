"""Gerador de resultado para Discord. Python 3, sem dependências externas."""
import json
import re
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkfont

APP_VERSION = '0.3.0'
DEFAULT_STATS_TEMPLATE = '**{jogador}{sub}**: {g}G {a}A {d}D {s}S {emoji} {posicao}'


def merge_contacts(current, baseline, saved):
    """Apply only this session's contact edits to the latest data on disk."""
    merged = {}
    for group in ('players','roles'):
        disk = saved.get(group,{})
        if not isinstance(disk,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in disk.items()):
            raise ValueError('O cadastro salvo está inválido. Importe um backup antes de salvar.')
        merged[group] = dict(disk)
        before,after = baseline.get(group,{}),current.get(group,{})
        for name in set(before)|set(after):
            if name not in after:
                merged[group].pop(name,None)
            elif name not in before or after[name]!=before[name]:
                merged[group][name]=after[name]
    return merged


class RoundedField(tk.Canvas):
    """Rounded shell with a border-free native input and normal keyboard support."""
    def __init__(self, parent, textvariable=None, width=12, values=None, state='normal', **kwargs):
        super().__init__(parent, height=38, width=max(80, width * 9), bg='#10131c', highlightthickness=0, bd=0)
        self.variable = textvariable or tk.StringVar()
        self.values = None if values is None else list(values)
        self.input = tk.Entry(self, textvariable=self.variable, bd=0, relief='flat',
                              bg='#1d2333', fg='#e9edf6', insertbackground='white',
                              readonlybackground='#1d2333', disabledbackground='#1d2333',
                              font=tkfont.nametofont('TkDefaultFont'), highlightthickness=0,
                              selectbackground='#4657bc', exportselection=False)
        self.arrow = None
        if self.values is not None:
            self.arrow = tk.Label(self,text='⌄',font=('Arial',14),bg='#1d2333',fg='#8d99bb',bd=0,cursor='hand2')
            self.arrow.bind('<Button-1>',self.open_menu)
            self.input.bind('<Alt-Down>',self.open_menu)
            self.input.bind('<Down>',self.open_menu)
            if state == 'readonly':
                self.input.bind('<Button-1>',self.open_menu)
        self.input.configure(state=state)
        self.bind('<Configure>', self.redraw)
        self.input.bind('<FocusIn>', lambda _: self.redraw())
        self.input.bind('<FocusOut>', lambda _: self.redraw())

    def redraw(self, _event=None):
        w, h, r = self.winfo_width(), 38, 12
        self.delete('shell')
        points = [r,0,w-r,0,w,0,w,r,w,h-r,w,h,w-r,h,r,h,0,h,0,h-r,0,r,0,0]
        self.create_polygon(points, smooth=True, fill='#1d2333', outline='', tags='shell')
        self.input.place(x=12, y=8, width=max(20, w-(44 if self.arrow else 24)), height=22)
        if self.arrow:
            self.arrow.place(x=max(0,w-30),y=5,width=24,height=26)

    def open_menu(self,_event=None):
        if self.input.cget('state')=='disabled' or not self.values:
            return 'break'
        if hasattr(self,'popup') and self.popup.winfo_exists():
            self.popup.destroy()
        popup = self.popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg='#222a3d')
        width = max(190,self.winfo_width())
        height = min(240,len(self.values)*27+8)
        x=min(self.winfo_rootx(),max(0,self.winfo_screenwidth()-width))
        y=self.winfo_rooty()+38
        if y+height>self.winfo_screenheight():
            y=max(0,self.winfo_rooty()-height)
        popup.geometry(f'{width}x{height}+{x}+{y}')
        listing = tk.Listbox(popup,bg='#222a3d',fg='#e9edf6',selectbackground='#4657bc',selectforeground='white',
                             font=tkfont.nametofont('TkDefaultFont'),bd=0,highlightthickness=0,activestyle='none',exportselection=False)
        bar = DarkScrollbar(popup,command=listing.yview)
        listing.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y')
        listing.pack(fill='both',expand=True,padx=4,pady=4)
        for value in self.values:
            listing.insert('end',value or '— Sem emoji —')
        if self.variable.get() in self.values:
            index=self.values.index(self.variable.get())
            listing.selection_set(index)
            listing.see(index)
        def choose(_event=None):
            selected=listing.curselection()
            if selected:
                self.variable.set(self.values[selected[0]])
            popup.destroy()
            self.input.focus_set()
        listing.bind('<ButtonRelease-1>',choose)
        listing.bind('<Return>',choose)
        listing.bind('<Escape>',lambda _:popup.destroy())
        def dismiss():
            if popup.winfo_exists():
                focused=popup.focus_get()
                if focused is None or not str(focused).startswith(str(popup)):
                    popup.destroy()
        popup.bind('<FocusOut>',lambda _:popup.after(100,dismiss))
        listing.focus_set()
        return 'break'

    def configure(self, cnf=None, **kwargs):
        if hasattr(self, 'input'):
            if 'values' in kwargs:
                self.values = list(kwargs.pop('values'))
            if 'state' in kwargs:
                self.input.configure(state=kwargs.pop('state'))
        return super().configure(cnf, **kwargs)


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text='', command=None, style='', **kwargs):
        super().__init__(parent, height=40, width=max(90, len(text)*8+28), bg='#10131c', bd=0, highlightthickness=0, takefocus=True, cursor='hand2')
        self.text, self.command, self.disabled = text, command, False
        self.accent = style == 'Accent.TButton'
        self.hover = False
        self.bind('<Configure>', self.redraw)
        self.bind('<Enter>', lambda _: self.set_hover(True))
        self.bind('<Leave>', lambda _: self.set_hover(False))
        self.bind('<Button-1>', self.invoke)
        self.bind('<Return>', self.invoke)
        self.bind('<space>', self.invoke)

    def set_hover(self, value):
        self.hover = value
        self.redraw()

    def redraw(self, _event=None):
        self.delete('all')
        w,h,r = self.winfo_width(),40,12
        color = '#303a53' if self.hover else '#222a3d'
        if self.accent:
            color = '#6674ff' if self.hover else '#5865f2'
        if self.disabled:
            color = '#222636'
        self.create_polygon([r,0,w-r,0,w,0,w,r,w,h-r,w,h,w-r,h,r,h,0,h,0,h-r,0,r,0,0], smooth=True, fill=color, outline='')
        self.create_text(w/2,h/2,text=self.text,fill='#737e98' if self.disabled else '#eef1ff',font=tkfont.nametofont('TkDefaultFont'))

    def invoke(self, _event=None):
        if not self.disabled and self.command:
            self.command()

    def configure(self, cnf=None, **kwargs):
        if 'state' in kwargs:
            self.disabled = kwargs.pop('state') == 'disabled'
            self.redraw()
        return super().configure(cnf, **kwargs)


class FlatNotebook(tk.Frame):
    """Simple page navigation without native notebook borders or focus outlines."""
    def __init__(self, parent):
        super().__init__(parent, bg='#10131c', bd=0, highlightthickness=0)
        self.pages, self.buttons, self.hidden, self.active = [], {}, set(), None
        self.nav = tk.Frame(self, bg='#10131c', bd=0)
        self.nav.pack(side='top', fill='x', pady=(0,10))

    def add(self, page, text=''):
        if page not in self.pages:
            self.pages.append(page)
            button = RoundedButton(self.nav, text=text, command=lambda p=page:self.select(p))
            self.buttons[page] = button
        self.hidden.discard(page)
        for p in self.pages:
            self.buttons[p].pack_forget()
            if p not in self.hidden:
                self.buttons[p].pack(side='left', padx=(0,6))
        if self.active is None:
            self.select(page)

    def select(self, page=None):
        if page is None:
            return str(self.active)
        if isinstance(page,int):
            page = self.pages[page]
        elif isinstance(page,str):
            page = next(p for p in self.pages if str(p)==page)
        if page in self.hidden:
            return
        if self.active is page:
            return
        if self.active is not None:
            self.active.pack_forget()
        self.active = page
        page.pack(side='top', fill='both', expand=True)
        for p,button in self.buttons.items():
            button.accent = p is page
            button.redraw()
        self.event_generate('<<NotebookTabChanged>>', when='tail')

    def index(self, page):
        if isinstance(page,int):
            return page
        return next(i for i,p in enumerate(self.pages) if str(p)==str(page))

    def hide(self,page):
        if isinstance(page,str):
            page = next(p for p in self.pages if str(p)==page)
        self.hidden.add(page)
        self.buttons[page].pack_forget()
        if self.active is page:
            self.select(next(p for p in self.pages if p not in self.hidden))
        page.pack_forget()


class DarkScrollbar(tk.Canvas):
    def __init__(self,parent,command=None,orient='vertical'):
        super().__init__(parent,bg='#10131c',highlightthickness=0,bd=0,
                         width=10 if orient=='vertical' else 100,
                         height=10 if orient=='horizontal' else 100)
        self.command,self.orient = command,orient
        self.first,self.last = 0.0,1.0
        self.drag_offset = 0
        self.bind('<Configure>',lambda _:self.draw())
        self.bind('<Button-1>',self.press)
        self.bind('<B1-Motion>',self.drag)

    def set(self,first,last):
        self.first,self.last=float(first),float(last)
        self.draw()

    def draw(self):
        self.delete('all')
        length = self.winfo_height() if self.orient=='vertical' else self.winfo_width()
        if self.last-self.first>=0.999:
            return
        start = self.first*length
        end = max(start+18,self.last*length)
        if self.orient=='vertical':
            self.create_line(5,start+4,5,end-4,width=5,fill='#39435b',capstyle='round')
        else:
            self.create_line(start+4,5,end-4,5,width=5,fill='#39435b',capstyle='round')

    def press(self,event):
        point = event.y if self.orient=='vertical' else event.x
        length = self.winfo_height() if self.orient=='vertical' else self.winfo_width()
        self.drag_offset = point-self.first*length if self.first*length<=point<=self.last*length else 0
        self.drag(event)

    def drag(self,event):
        length = self.winfo_height() if self.orient=='vertical' else self.winfo_width()
        point = event.y if self.orient=='vertical' else event.x
        if self.command:
            self.command('moveto',max(0,min(1,(point-self.drag_offset)/max(1,length))))


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

# Sets — Primeiro a 3 vitórias
{sets}

# Stats — {time1}
{stats1}

# Stats — {time2}
{stats2}

{stats_por_partida}

{hms}
{ping_resultados}"""


def number(raw, label):
    if not re.fullmatch(r'[0-9]+', raw.strip()):
        raise ValueError(label + ': informe um número inteiro de zero ou mais.')
    return int(raw)


def series_result(sets, teams, best_of=3):
    target = best_of // 2 + 1
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
        if index > best_of or max(wins) == target:
            raise ValueError(f'A série termina em {target} vitórias. Deixe partidas não jogadas vazias.')
        sa, sb = number(a, f'Set {index}, time 1'), number(b, f'Set {index}, time 2')
        if sa == sb:
            raise ValueError(f'Set {index}: informe o placar final sem empate.')
        winner = 0 if sa > sb else 1
        wins[winner] += 1
        line = f'{index}º set: {teams[0]} {sa} — {sb} {teams[1]} | Win: **{teams[winner]}**'
        if item.get('mvp', '').strip():
            line += ' | MVP: **' + item['mvp'].strip() + '**'
        lines.append(line)
    winner = teams[wins.index(target)] if target in wins else 'Em andamento'
    return wins, winner, '\n'.join(lines) or 'Nenhum set informado.'


def stats_text(rows, template=DEFAULT_STATS_TEMPLATE):
    lines = []
    for row in rows:
        player = row['player'].strip()
        if not player:
            if any(row.get(k, '').strip() not in ('', '0') for k in ('g', 'a', 'd', 's', 'emoji', 'position')):
                raise ValueError('Selecione o jogador da linha de estatísticas preenchida.')
            continue
        counts = [number(row.get(k, '').strip() or '0', 'Stats ' + player) for k in ('g', 'a', 'd', 's')]
        sub = ' (sub)' if row.get('sub') else ''
        fields=dict(jogador=player,sub=sub,g=str(counts[0]),a=str(counts[1]),d=str(counts[2]),s=str(counts[3]),emoji=row.get('emoji','').strip(),posicao=row.get('position','').strip())
        lines.append(re.sub(r'\{([a-z0-9_]+)\}',lambda m:fields.get(m[1],m[0]),template).rstrip())
    return '\n'.join(lines) or 'Sem estatísticas informadas.'


def aggregate_stats(matches):
    totals=[{},{}]
    for teams in matches:
        for team,rows in enumerate(teams):
            stats_text(rows)  # Validate missing players and numeric counts before summing.
            for row in rows:
                player=row['player'].strip()
                if not player:
                    continue
                if player not in totals[team]:
                    totals[team][player]=dict(player=player,g='0',a='0',d='0',s='0',emoji=row.get('emoji',''),position=row.get('position',''),sub=row.get('sub',False))
                total=totals[team][player]
                for key in ('g','a','d','s'):
                    total[key]=str(int(total[key])+number(row.get(key,'').strip() or '0','Stats '+player))
                for key in ('emoji','position'):
                    if row.get(key,'').strip():
                        total[key]=row[key].strip()
                total['sub']=total['sub'] and row.get('sub',False)
    return [list(team.values()) for team in totals]


def generate_extended(values, hms, template, sets, stats, match_stats=None, stats_template=DEFAULT_STATS_TEMPLATE):
    wins, winner, set_lines = series_result(sets, [values['time1'], values['time2']], best_of=5)
    match_sections=[]
    match_fields={}
    if match_stats is not None:
        for index,teams in enumerate(match_stats):
            played=index<len(sets) and bool(sets[index]['a'].strip() or sets[index]['b'].strip())
            has_stats=any(row.get('player','').strip() or any(row.get(k,'').strip() not in ('','0') for k in ('g','a','d','s','emoji','position')) for rows in teams for row in rows)
            if not played and has_stats:
                raise ValueError(f'Informe o placar da partida {index+1} antes de usar as stats dela.')
            if not played:
                continue
            text1,text2=stats_text(teams[0],stats_template),stats_text(teams[1],stats_template)
            section=f'## Partida {index+1} — Stats\n### {values["time1"]}\n{text1}\n### {values["time2"]}\n{text2}'
            match_sections.append(section)
            match_fields[f'partida{index+1}_stats1']=text1
            match_fields[f'partida{index+1}_stats2']=text2
        stats=aggregate_stats(match_stats)
    for index,item in enumerate(sets,1):
        if item['a'].strip() and item['b'].strip():
            match_fields[f'partida{index}_placar']=item['a'].strip()+' — '+item['b'].strip()
            match_fields[f'partida{index}_vencedor']=values['time1'] if int(item['a'])>int(item['b']) else values['time2']
            match_fields[f'partida{index}_mvp']=item.get('mvp','')
    for i in range(1,6):
        for key in ('stats1','stats2','placar','vencedor','mvp'):
            match_fields.setdefault(f'partida{i}_{key}','')
    values = dict(values, placar1=str(wins[0]), placar2=str(wins[1]))
    base, _ = generate(values, hms, '{motm}')
    data = dict(values, vencedor=winner, tipo=values.get('tipo', 'RANKED'), sets=set_lines,
                stats1=stats_text(stats[0],stats_template), stats2=stats_text(stats[1],stats_template),stats_por_partida='\n\n'.join(match_sections),**match_fields)
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
        for name in ('TkDefaultFont', 'TkTextFont', 'TkMenuFont'):
            tkfont.nametofont(name).configure(family=self.sans, size=10)
        self.title('ALSA Match Results')
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
        self.loaded_contacts = {'players': {}, 'roles': {}}
        self.pickers = {}
        self.score_widgets = {}
        self.extra_pickers = []
        self.set_rows = []
        self.stat_rows = [[], []]
        self.match_stat_rows = [[[], []] for _ in range(5)]
        self.stat_row_frames = {}
        self.preview_edited = False
        self.stats_template = tk.StringVar(value=DEFAULT_STATS_TEMPLATE)
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
        style.configure('TPanedwindow', background='#10131c')
        style.configure('TLabel', background='#10131c', foreground='#e9edf6', font=(self.sans, 10))
        style.configure('TButton', padding=(12, 9), background='#252c40', borderwidth=0)
        style.map('TButton', background=[('active', '#354360')])
        style.configure('Accent.TButton', background='#5865f2', foreground='white', font=(self.sans, 11, 'bold'))
        style.map('Accent.TButton', background=[('active', '#4752c4')])
        style.configure('TEntry', fieldbackground='#1d2333', foreground='#e9edf6', insertcolor='white', padding=6)
        style.layout('Minimal.TCombobox', [('Combobox.padding', {'sticky': 'nswe', 'children': [('Combobox.downarrow', {'side': 'right', 'sticky': 'ns'}), ('Combobox.textarea', {'sticky': 'nswe'})]})])
        style.configure('Minimal.TCombobox', fieldbackground='#1d2333', background='#1d2333', foreground='#e9edf6', arrowcolor='#8d99bb', borderwidth=0, padding=0)
        style.map('Minimal.TCombobox', fieldbackground=[('readonly', '#1d2333')], foreground=[('readonly', '#e9edf6')], selectbackground=[('!disabled', '#4657bc')])
        style.layout('TButton', [('Button.padding', {'sticky': 'nswe', 'children': [('Button.label', {'sticky': 'nswe'})]})])
        style.layout('TNotebook.Tab', [('Notebook.tab', {'sticky': 'nswe', 'children': [('Notebook.padding', {'side': 'top', 'sticky': 'nswe', 'children': [('Notebook.label', {'side': 'top', 'sticky': ''})]})]})])
        style.configure('TCombobox', fieldbackground='#1d2333', background='#252c40', foreground='#e9edf6', arrowcolor='#b4c3ff', padding=6)
        style.map('TCombobox', fieldbackground=[('readonly', '#1d2333')], foreground=[('readonly', '#e9edf6')])
        style.map('TEntry', fieldbackground=[('readonly', '#202738')], foreground=[('readonly', '#a9b8df')])
        style.configure('TNotebook', background='#10131c', borderwidth=0)
        style.configure('TNotebook.Tab', padding=(14, 10), background='#1d2333', foreground='#aeb8d0')
        style.map('TNotebook.Tab', background=[('selected', '#5865f2')], foreground=[('selected', 'white')])
        style.configure('TLabelframe', background='#10131c', bordercolor='#10131c', borderwidth=0, relief='flat')
        style.configure('TLabelframe.Label', foreground='#a9b8ff', background='#10131c', font=(self.sans, 11, 'bold'))
        style.configure('Treeview', background='#1d2333', fieldbackground='#1d2333', foreground='#e9edf6', rowheight=30)
        style.layout('Treeview',[('Treeview.treearea',{'sticky':'nswe'})])
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
        self.mode_tabs = FlatNotebook(outer)
        self.mode_tabs.pack(fill='x', pady=(0, 16))
        for name, description in [('Amistoso', 'Placar direto, destaques e HMs. Ideal para amistosos e scrims.'), ('Ranked / Detalhe', 'Primeiro a 3 vitórias • até 5 partidas • estatísticas dos dois times.')]:
            page = ttk.Frame(self.mode_tabs, padding=12)
            ttk.Label(page, text=description, foreground='#b5c1df').pack(anchor='w')
            self.mode_tabs.add(page, text=name)
        self.mode_tabs.bind('<<NotebookTabChanged>>', self.change_mode)
        footer = ttk.Frame(outer, padding=(0, 12, 0, 0))
        footer.pack(side='bottom', fill='x')
        footer.columnconfigure(0, weight=1)
        footer.columnconfigure(2, weight=1)
        ttk.Label(footer, text=f'ALSA Match Results · v{APP_VERSION}', foreground='#7e8aa8', font=(self.mono, 9)).grid(row=0, column=1)
        RoundedButton(footer, text='Dúvidas / FAQ', command=self.show_faq).grid(row=0, column=2, sticky='e')
        panes = ttk.Panedwindow(outer, orient='horizontal')
        panes.pack(fill='both', expand=True)
        left_container = ttk.Frame(panes)
        input_tabs = FlatNotebook(left_container)
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
        panes.after_idle(lambda:panes.sashpos(0,int(panes.winfo_width()*0.48)))
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
        tabs = FlatNotebook(right)
        tabs.pack(fill='both', expand=True)
        preview_tab, template_tab = ttk.Frame(tabs), ttk.Frame(tabs)
        tabs.add(preview_tab, text='Prévia')
        tabs.add(template_tab, text='Templates')
        contacts_tab = ttk.Frame(tabs, padding=8)
        tabs.add(contacts_tab, text='Cadastros')
        self.build_contacts(contacts_tab)
        preview_controls = ttk.Frame(preview_tab)
        preview_controls.pack(fill='x',pady=(0,8))
        RoundedButton(preview_controls,text='Gerar novamente',command=self.regenerate_preview).pack(side='right')
        ttk.Label(preview_controls,text='Edite o texto final aqui.',foreground='#aeb8d0').pack(side='left')
        self.preview = self.text_area(preview_tab)
        self.preview.bind('<<Modified>>',self.preview_modified)
        RoundedButton(template_tab,text='Abrir editor em tela ampla',command=self.open_templates,style='Accent.TButton').pack(anchor='center',pady=24)
        ttk.Label(template_tab,text='Templates separados, com marcadores em uma faixa rolável.',wraplength=400).pack(anchor='center')
        self.template_window = tk.Toplevel(self)
        self.template_window.title('Templates • ALSA Match Results')
        self.template_window.configure(bg='#10131c')
        self.template_window.geometry('1100x800')
        self.template_window.withdraw()
        self.template_window.protocol('WM_DELETE_WINDOW',self.template_window.withdraw)
        self.template_window.iconphoto(True,self.window_icon)
        template_shell = ttk.Frame(self.template_window,padding=20)
        template_shell.pack(fill='both',expand=True)
        template_footer = ttk.Frame(template_shell)
        template_footer.pack(side='bottom',fill='x',pady=(12,0))
        RoundedButton(template_footer,text='Voltar à partida',command=self.template_window.withdraw).pack(side='right')
        self.template_status = tk.StringVar(value='Cada formato tem seu próprio template salvo.')
        ttk.Label(template_footer,textvariable=self.template_status).pack(side='left')
        self.template_tabs = FlatNotebook(template_shell)
        self.template_tabs.pack(fill='both', expand=True)
        self.template = self.build_template_editor('Template Amistoso', DEFAULT_TEMPLATE, False)
        self.ranked_template = self.build_template_editor('Template Ranked', RANKED_TEMPLATE, True)
        tabs.bind('<<NotebookTabChanged>>',lambda _:self.open_templates() if tabs.index(tabs.select())==1 else None)
        self.status = tk.StringVar()
        ttk.Label(footer, textvariable=self.status, wraplength=700, foreground='#aeb8d0').grid(row=1,column=0,columnspan=3,sticky='w',pady=(8,0))
        self.copy_button = RoundedButton(footer, text='Copiar mensagem', style='Accent.TButton', command=self.copy)
        self.copy_button.grid(row=0,column=0,sticky='w')
        RoundedButton(right, text='Importar cadastros da versão anterior', command=self.import_preferences).pack(fill='x', pady=(8, 0))
        self.load_preferences()
        self.refresh_contacts()
        self.update_preview()
        self.change_mode()
        self.protocol('WM_DELETE_WINDOW', self.close)

    def open_templates(self):
        self.template_window.deiconify()
        self.template_window.state('zoomed')
        self.template_window.lift()

    def entry(self, parent, key, row, column, span=1, initial=''):
        var = tk.StringVar(value=initial)
        self.vars[key] = var
        if key.endswith('_emoji'):
            widget = RoundedField(parent, textvariable=var, values=EMOJIS)
        elif key in ('time1', 'time2') or key in dict(AWARDS):
            widget = RoundedField(parent, textvariable=var, values=())
            self.pickers[key] = widget
        else:
            widget = RoundedField(parent, textvariable=var)
        widget.grid(row=row, column=column, columnspan=span, sticky='ew', padx=4, pady=4)
        if key in ('placar1', 'placar2'):
            self.score_widgets[key] = widget
        var.trace_add('write', lambda *_: self.update_preview())

    def text_area(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True)
        text = tk.Text(frame, width=1, wrap='word', font=(self.mono, 11), undo=True, bg='#171c29', fg='#dbe4fa', insertbackground='white', relief='flat', bd=0, highlightthickness=0, padx=16, pady=14, selectbackground='#5865f2')
        bar = DarkScrollbar(frame, command=text.yview)
        text.configure(yscrollcommand=bar.set)
        bar.pack(side='right', fill='y')
        text.pack(fill='both', expand=True)
        return text

    def scroll_frame(self, parent):
        container = ttk.Frame(parent)
        canvas = tk.Canvas(container, highlightthickness=0, bg='#10131c')
        bar = DarkScrollbar(container, orient='vertical', command=canvas.yview)
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
        self.template_tabs.select(1 if ranked else 0)
        if ranked:
            self.input_tabs.add(self.details_page, text='Sets e estatísticas')
        else:
            for key, score in zip(('placar1', 'placar2'), self.friendly_scores):
                self.vars[key].set(score)
            self.input_tabs.select(0)
            self.input_tabs.hide(self.details_page)
        self.update_preview()

    def build_template_editor(self, title, default, ranked):
        page = ttk.Frame(self.template_tabs, padding=10)
        self.template_tabs.add(page, text=title)
        help_text = ('{sets}: placares e vencedor de cada partida\n{stats1} / {stats2}: totais dos dois times; {stats_por_partida}: detalhes\n{partida1_stats1} etc.: stats de uma partida específica\n{mvps} {mvas} {mvds} {gks}: listas de premiados\n{refs_linha}: árbitro · {ping_resultados}: ping final' if ranked else
                     '{motm}, {mvp1}, {mvp2}, {mva1}, {mva2},\n{mvd1}, {mvd2}, {gk}: jogador + emoji')
        ttk.Label(page, text=help_text, wraplength=450, foreground='#aeb8d0').pack(anchor='w', pady=(0, 8))
        ttk.Label(page, text='Clique num marcador para inserir no cursor.', foreground='#aeb8d0').pack(anchor='w')
        marker_shell = ttk.Frame(page)
        marker_shell.pack(fill='x',pady=8)
        strip = tk.Canvas(marker_shell,height=44,bg='#10131c',highlightthickness=0,bd=0)
        strip.pack(fill='x')
        marker_scroll = DarkScrollbar(marker_shell,orient='horizontal',command=strip.xview)
        marker_scroll.pack(fill='x',pady=(4,0))
        strip.configure(xscrollcommand=marker_scroll.set)
        markers = ttk.Frame(strip)
        strip.create_window((0,0),window=markers,anchor='nw')
        markers.bind('<Configure>',lambda _:strip.configure(scrollregion=strip.bbox('all')))
        strip.bind('<MouseWheel>',lambda event:strip.xview_scroll(-int(event.delta/120),'units'))
        names = ['time1','time2','placar1','placar2','vencedor','hms'] + (['sets','stats1','stats2','stats_por_partida'] + [f'partida{n}_{field}' for n in range(1,6) for field in ('stats1','stats2','placar','vencedor','mvp')] + ['mvps','mvas','mvds','gks','refs_linha','motm_linha','ping_resultados'] if ranked else ['motm','mvp1','mvp2','mva1','mva2','mvd1','mvd2','gk'])
        if ranked:
            ttk.Label(page,text='Formato de cada jogador: {jogador} {sub} {g} {a} {d} {s} {emoji} {posicao}',foreground='#aeb8d0').pack(anchor='w')
            RoundedField(page,textvariable=self.stats_template,width=60).pack(fill='x',pady=(4,8))
            self.stats_template.trace_add('write',lambda *_:self.update_preview())
        editor = self.text_area(page)
        editor.insert('1.0', default)
        editor.bind('<<Modified>>', self.modified)
        for index, key in enumerate(names):
            def insert(k=key):
                editor.insert('insert', '{' + k + '}')
                editor.focus_set()
            RoundedButton(markers, text='{' + key + '}', command=insert).pack(side='left',padx=(0,6))
        controls = ttk.Frame(page)
        controls.pack(fill='x', pady=(10,0))
        def restore():
            editor.delete('1.0','end')
            editor.insert('1.0',default)
            self.update_preview()
        RoundedButton(controls, text='Restaurar', command=restore).pack(side='left')
        def save():
            if self.save_preferences():
                self.status.set(title + ' salvo. Os dois formatos são guardados separadamente.')
                self.template_status.set(title + ' salvo.')
        RoundedButton(controls, text='Salvar template', command=save, style='Accent.TButton').pack(side='right')
        return editor

    def show_faq(self):
        if hasattr(self, 'faq_window') and self.faq_window.winfo_exists():
            self.faq_window.lift()
            return
        win = self.faq_window = tk.Toplevel(self)
        win.title('Dúvidas • ALSA Match Results')
        win.geometry('650x650')
        win.configure(bg='#10131c')
        win.iconphoto(True, self.window_icon)
        content = self.scroll_frame(win)
        content.master.master.pack(fill='both', expand=True)
        ttk.Label(content, text='Como podemos ajudar?', font=(self.sans,18,'bold')).pack(anchor='w', pady=12)
        questions = [
            ('Como pego o ID de um jogador?', 'No Discord: Configurações do usuário → Avançado → ative Modo desenvolvedor. Clique com o botão direito no NOME da pessoa (na mensagem ou lista de membros) → Copiar ID do usuário. Em Jogadores e cargos, selecione Jogador e cole o número. O app cria <@ID>.'),
            ('Como pego o ID de um cargo?', 'Com o Modo desenvolvedor ativo e acesso às configurações do servidor: Configurações do servidor → Cargos → menu do cargo → Copiar ID do cargo. Cadastre como Cargo / time; o app cria <@&ID>. Se não tiver acesso, peça o ID ao administrador da liga.'),
            ('Posso usar Copiar ID da mensagem?', 'Não. O ID da mensagem identifica a mensagem, não a pessoa nem o cargo. Para jogador, copie o ID do usuário; para time, copie o ID do cargo. Digitar apenas @nome também não gera o ping.'),
            ('Como funciona o placar Ranked?', 'Cada partida soma uma vitória para quem marcou mais gols. Ex.: 3–1 em gols soma 1–0 na série. Quem vencer 3 partidas ganha a série. Ela termina em 3–0, 3–1 ou 3–2. Use + Adicionar partida para incluir a quarta ou quinta. Pare na terceira vitória.'),
            ('Como salvo o REF e o ping de resultados?', 'Cadastre o árbitro como Jogador. No Ranked, selecione seu nome no campo REF. O ping final é texto livre: cole <@&ID> para cargo ou <@ID> para usuário. Ele fica salvo ao salvar as preferências ou fechar o app.'),
            ('Como edito e salvo os dois templates?', 'Abra Editar template. Escolha Template Amistoso ou Template Ranked. Os botões de marcadores inserem o campo no cursor. No Ranked, use {sets}, {stats1}, {stats2} e as listas de premiados. Clique Salvar template. Cada formato fica salvo separadamente.'),
            ('Como edito stats e a mensagem final?', 'Em Sets e estatísticas, escolha Por partida e selecione a partida para preencher os dois times. Os totais são somados por jogador. No Template Ranked, {stats_por_partida} inclui todas as partidas; {partida1_stats1} inclui só o time 1 da primeira partida (até partida5). O formato de cada jogador também é editável. Para exceções, edite diretamente a Prévia. Copiar usa esse texto. Gerar novamente descarta as edições e aplica os campos atuais.'),
            ('Como copio e envio o resultado?', 'Clique Copiar mensagem para o Discord e cole com Ctrl+V no canal da liga. A prévia mostra o markdown em texto. O Discord transforma pings e emojis válidos na mensagem enviada.'),
            ('Onde ficam meus dados?', f'Local neste computador: {self.state_file}\n\nJogadores, cargos, templates e ping final ficam em %APPDATA%\\ResultadoDaLiga\\preferencias.json. Atualizar o executável preserva esse arquivo. Stats e campos da partida não são salvos ao fechar.')]
        for title, answer in questions:
            card = ttk.Frame(content, padding=(0,6))
            card.pack(fill='x')
            body = ttk.Label(card, text=answer, wraplength=550, padding=12, foreground='#b5c1df')
            opened = [False]
            def toggle(b=body, state=opened):
                state[0] = not state[0]
                if state[0]: b.pack(fill='x')
                else: b.pack_forget()
            RoundedButton(card, text=title, command=toggle).pack(fill='x')

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
            widget = RoundedField(parent, textvariable=var, values=(), width=width)
            self.extra_pickers.append(widget)
        elif kind == 'emoji':
            widget = RoundedField(parent, textvariable=var, values=EMOJIS, width=width)
        else:
            widget = RoundedField(parent, textvariable=var, width=width)
        var.trace_add('write', lambda *_: self.update_preview())
        return var, widget

    def build_details(self, parent):
        self.tipo = tk.StringVar(value='RANKED')
        self.refs, widget = self.detail_var(parent, kind='player')
        ttk.Label(parent, text='REF (selecione um jogador salvo ou cole o ping)').pack(anchor='w')
        widget.pack(fill='x', pady=4)
        self.results_ping, widget = self.detail_var(parent)
        ttk.Label(parent, text='Ping de resultados (opcional)').pack(anchor='w')
        widget.pack(fill='x', pady=4)
        ttk.Label(parent, text='Primeiro a 3 vitórias: até 5 partidas.\nEx.: vencer 3–1 em gols soma UMA vitória na série.\nPare em 3–0, 3–1 ou 3–2; deixe partidas restantes vazias.', wraplength=430).pack(anchor='w', pady=8)
        self.set_container = ttk.Frame(parent)
        self.set_container.pack(fill='x')
        self.add_set_button = RoundedButton(parent, text='+ Adicionar partida', command=self.add_set)
        self.add_set_button.pack(fill='x', pady=6)
        for _ in range(3):
            self.add_set()
        ttk.Label(parent, text='G = gols; A = assistências; D = defesas/desarmes; S = saves.\nEscolha totais ou preencha cada partida para somar automaticamente.', wraplength=430).pack(anchor='w', pady=8)
        self.stats_mode = tk.StringVar(value='Totais da série')
        self.stats_scope = tk.StringVar(value='Partida 1')
        RoundedField(parent,textvariable=self.stats_mode,values=['Totais da série','Por partida (soma automática)']).pack(fill='x',pady=4)
        self.stats_scope_picker = RoundedField(parent,textvariable=self.stats_scope,values=[f'Partida {n}' for n in range(1,4)])
        self.stats_scope_picker.pack(fill='x',pady=4)
        self.stat_frames=[]
        for team in range(2):
            frame = ttk.LabelFrame(parent, text=f'Estatísticas do time {team + 1}', padding=6)
            frame.pack(fill='x', pady=6)
            self.stat_frames.append(frame)
            RoundedButton(frame, text='+ Adicionar jogador', command=lambda t=team, f=frame: self.add_stat(t, f)).pack(fill='x')
        self.stats_mode.trace_add('write',lambda *_:self.show_stat_scope())
        self.stats_scope.trace_add('write',lambda *_:self.show_stat_scope())
        self.show_stat_scope()

    def current_stats(self):
        return self.stat_rows if self.stats_mode.get()=='Totais da série' else self.match_stat_rows[int(self.stats_scope.get().split()[-1])-1]

    def show_stat_scope(self):
        for frame in self.stat_row_frames.values():
            frame.pack_forget()
        buckets=self.current_stats()
        for team,rows in enumerate(buckets):
            if not rows:
                self.add_stat(team,self.stat_frames[team])
            for row in rows:
                self.stat_row_frames[id(row)].pack(fill='x')
        self.update_preview()

    def add_set(self):
        if len(self.set_rows) >= 5:
            return
        frame = ttk.LabelFrame(self.set_container, text=f'Partida {len(self.set_rows)+1}', padding=10)
        frame.pack(fill='x', pady=6)
        row = {}
        for col, (key,label,kind) in enumerate([('a','Gols time 1','text'),('b','Gols time 2','text'),('mvp','MVP opcional','player')]):
            ttk.Label(frame,text=label).grid(row=0,column=col,sticky='w',pady=(0,4))
            row[key], widget = self.detail_var(frame,kind=kind)
            widget.grid(row=1,column=col,sticky='ew',padx=3)
            frame.columnconfigure(col,weight=1)
        self.set_rows.append(row)
        if hasattr(self,'stats_scope_picker'):
            self.stats_scope_picker.configure(values=[f'Partida {n}' for n in range(1,len(self.set_rows)+1)])
        self.add_set_button.configure(state='disabled' if len(self.set_rows)==5 else 'normal')
        for picker in self.extra_pickers:
            picker.configure(values=sorted(self.contacts['players'], key=str.casefold))

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
        bucket=self.current_stats()[team]
        bucket.append(row)
        self.stat_row_frames[id(row)]=frame
        def remove():
            bucket.remove(row)
            self.stat_row_frames.pop(id(row),None)
            self.extra_pickers[:] = [p for p in self.extra_pickers if p.winfo_exists() and not str(p).startswith(str(frame) + '.')]
            frame.destroy()
            self.update_preview()
        RoundedButton(frame, text='Remover', command=remove).grid(row=5, column=3)
        for picker in self.extra_pickers:
            picker.configure(values=sorted(self.contacts['players'], key=str.casefold))

    def modified(self, event):
        if event.widget.edit_modified():
            event.widget.edit_modified(False)
            self.update_preview()

    def preview_modified(self,event):
        if event.widget.edit_modified():
            event.widget.edit_modified(False)
            self.preview_edited=True
            self.valid_message=self.preview.get('1.0','end-1c')
            self.copy_button.configure(state='normal' if self.valid_message else 'disabled')
            self.status.set('Prévia editada. Copiar usa este texto; Gerar novamente substitui as edições.')

    def regenerate_preview(self):
        self.preview_edited=False
        self.update_preview()

    def update_preview(self):
        if not hasattr(self, 'copy_button'):
            return
        if self.preview_edited:
            self.status.set('Prévia editada preservada. Use Gerar novamente para aplicar alterações dos campos.')
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
                values.update(tipo=self.tipo.get(), refs=resolve(self.refs.get()), ping_resultados=self.results_ping.get())
                match_stats = [[[ {k: resolve(v.get()) if k=='player' else v.get() for k,v in row.items()} for row in rows] for rows in game] for game in self.match_stat_rows] if self.stats_mode.get()!='Totais da série' else None
                message, winner, wins = generate_extended(values, self.hms.get('1.0', 'end-1c'), self.ranked_template.get('1.0', 'end-1c'), sets, stats, match_stats, self.stats_template.get())
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
        self.preview.edit_modified(False)

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
            data = json.loads(self.state_file.read_text(encoding='utf-8-sig'))
            for group in self.contacts:
                saved = data.get(group, {})
                if isinstance(saved, dict):
                    self.contacts[group] = {k: v for k, v in saved.items() if isinstance(k, str) and isinstance(v, str)}
            if isinstance(data.get('template'), str):
                self.template.delete('1.0', 'end')
                self.template.insert('1.0', data['template'])
            if isinstance(data.get('ranked_template'), str):
                self.ranked_template.delete('1.0', 'end')
                saved_template=data['ranked_template'].replace('# Sets — Melhor de 3', '# Sets — Primeiro a 3 vitórias')
                if saved_template==RANKED_TEMPLATE.replace('{stats_por_partida}\n\n',''):
                    saved_template=RANKED_TEMPLATE
                self.ranked_template.insert('1.0',saved_template)
            if isinstance(data.get('stats_template'),str):
                self.stats_template.set(data['stats_template'])
            if isinstance(data.get('results_ping'), str):
                self.results_ping.set(data['results_ping'])
        except (OSError, ValueError, AttributeError):
            pass
        self.loaded_contacts = {group:dict(items) for group,items in self.contacts.items()}

    def build_contacts(self, parent):
        ttk.Label(parent, text='Cadastre uma vez e selecione pelo nome nos campos da partida.', wraplength=400).pack(anchor='w', pady=6)
        controls=ttk.Frame(parent)
        controls.pack(fill='x',pady=(0,8))
        RoundedButton(controls,text='Recarregar cadastros',command=self.reload_contacts).pack(side='left',padx=(0,6))
        RoundedButton(controls,text='Abrir pasta de dados',command=lambda:os.startfile(self.state_file.parent)).pack(side='left')
        self.contact_kind = tk.StringVar(value='Jogador')
        RoundedField(parent, textvariable=self.contact_kind, values=('Jogador', 'Cargo / time'), state='readonly').pack(fill='x', pady=4)
        ttk.Label(parent, text='Nome para reconhecer (ex.: Vielism ou Requiem)').pack(anchor='w')
        self.contact_name = tk.StringVar()
        RoundedField(parent, textvariable=self.contact_name).pack(fill='x', pady=4)
        ttk.Label(parent, text='ID ou ping (ex.: 123456789 ou <@123456789>)').pack(anchor='w')
        self.contact_ping = tk.StringVar()
        RoundedField(parent, textvariable=self.contact_ping).pack(fill='x', pady=4)
        RoundedButton(parent, text='Salvar / atualizar', command=self.save_contact).pack(fill='x', pady=6)
        self.contact_list = ttk.Treeview(parent, columns=('kind', 'name', 'ping'), show='headings', selectmode='browse', height=8)
        for col, label, width in [('kind', 'Tipo', 70), ('name', 'Nome', 110), ('ping', 'Ping', 170)]:
            self.contact_list.heading(col, text=label)
            self.contact_list.column(col, width=width)
        self.contact_list.pack(fill='both', expand=True)
        self.contact_list.bind('<<TreeviewSelect>>', self.select_contact)
        RoundedButton(parent, text='Excluir selecionado', command=self.delete_contact).pack(fill='x', pady=6)

    def reload_contacts(self):
        try:
            data=json.loads(self.state_file.read_text(encoding='utf-8-sig'))
            contacts=merge_contacts({'players':{},'roles':{}},{'players':{},'roles':{}},data)
        except (OSError,ValueError) as error:
            messagebox.showerror('Não foi possível carregar',str(error))
            return
        self.contacts=contacts
        self.loaded_contacts={group:dict(items) for group,items in contacts.items()}
        self.refresh_contacts()
        self.status.set('Jogadores e cargos recarregados do arquivo de preferências.')

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
            if self.refs.get() == name:
                self.refs.set(ping)
            for row in self.set_rows:
                if row['mvp'].get() == name:
                    row['mvp'].set(ping)
            for rows in self.stat_rows + [rows for game in self.match_stat_rows for rows in game]:
                for row in rows:
                    if row['player'].get() == name:
                        row['player'].set(ping)
        self.refresh_contacts()

    def save_preferences(self):
        try:
            saved=json.loads(self.state_file.read_text(encoding='utf-8-sig')) if self.state_file.exists() else {}
            if not isinstance(saved,dict):
                raise ValueError('O arquivo de preferências está inválido.')
            contacts=merge_contacts(self.contacts,self.loaded_contacts,saved)
            data = {'template': self.template.get('1.0', 'end-1c'), **contacts}
            if hasattr(self, 'ranked_template'):
                data['ranked_template'] = self.ranked_template.get('1.0', 'end-1c')
            if hasattr(self, 'results_ping'):
                data['results_ping'] = self.results_ping.get()
            data['stats_template']=self.stats_template.get()
            temporary = self.state_file.with_suffix('.tmp')
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            if self.state_file.exists():
                import shutil
                shutil.copy2(self.state_file,self.state_file.with_name('preferencias.backup.json'))
            temporary.replace(self.state_file)
        except (OSError,ValueError) as error:
            messagebox.showwarning('Não foi possível salvar', 'Seus dados existentes foram preservados.\n'+str(error))
            return False
        self.contacts=contacts
        self.loaded_contacts={group:dict(items) for group,items in contacts.items()}
        return True

    def close(self):
        if self.save_preferences():
            self.destroy()


if __name__ == '__main__':
    App().mainloop()
