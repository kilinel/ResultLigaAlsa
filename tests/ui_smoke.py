"""Windows CI: exercise modes, saved contacts, stats, clipboard and persistence."""
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from resultado_app import App

with tempfile.TemporaryDirectory() as folder:
    os.environ['APPDATA'] = folder
    app = App()
    try:
        app.update()
        assert app.window_icon.width() == 256
        assert app.header_logo.width() <= 80
        app.contacts['roles'] = {'Alpha': '<@&1>', 'Beta': '<@&2>'}
        app.contacts['players'] = {'Player': '<@7>'}
        app.refresh_contacts()
        app.vars['time1'].set('Alpha')
        app.vars['time2'].set('Beta')
        app.vars['placar1'].set('3')
        app.vars['placar2'].set('1')
        assert app.winner.get() == '<@&1>'
        app.mode_tabs.select(1)
        app.change_mode()
        app.refs.set('Player')
        for row, a, b in [(app.set_rows[0], '3', '1'), (app.set_rows[1], '2', '0'), (app.set_rows[2], '1', '0')]:
            row['a'].set(a)
            row['b'].set(b)
        app.stat_rows[0][0]['player'].set('Player')
        app.stat_rows[0][0]['g'].set('5')
        app.stat_rows[1][0]['player'].set('<@8>')
        app.update()
        assert 'Resultado: 3-0' in app.valid_message
        assert 'REFS: **<@7>**' in app.valid_message
        app.add_set()
        app.add_set()
        app.add_set()
        assert len(app.set_rows) == 5
        app.show_faq()
        app.update()
        assert app.faq_window.winfo_exists()
        app.faq_window.destroy()
        assert '**<@7>**: 5G' in app.valid_message
        assert '**<@8>**' in app.valid_message
        app.copy()
        assert app.clipboard_get() == app.valid_message
        app.mode_tabs.select(0)
        app.change_mode()
        app.update()
        assert 'MATCH RESULT' in app.valid_message
        assert app.save_preferences()
        data = json.loads(app.state_file.read_text(encoding='utf-8'))
        assert data['players']['Player'] == '<@7>'
        assert 'ranked_template' in data
        app.template.insert('end','\nAMISTOSO CUSTOM')
        app.ranked_template.insert('end','\nRANKED CUSTOM')
        app.results_ping.set('<@&99>')
        assert app.save_preferences()
        print('PASS: tabs, contact resolution, series, both teams, clipboard and persistence')
    finally:
        app.destroy()
    restored = App()
    try:
        assert 'AMISTOSO CUSTOM' in restored.template.get('1.0','end')
        assert 'RANKED CUSTOM' in restored.ranked_template.get('1.0','end')
        assert restored.results_ping.get() == '<@&99>'
    finally:
        restored.destroy()
