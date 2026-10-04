import unittest
from resultado_app import series_result, stats_text, generate, generate_extended, RANKED_TEMPLATE, merge_contacts


def sets(*scores):
    return [dict(a=str(a), b=str(b), mvp='<@7>') for a, b in scores]


class ResultsTests(unittest.TestCase):
    def test_series_winners(self):
        self.assertEqual(series_result(sets((3, 1), (2, 4), (5, 2)), ['A', 'B'])[:2], ([2, 1], 'A'))
        self.assertEqual(series_result(sets((0, 3), (1, 2)), ['A', 'B'])[:2], ([0, 2], 'B'))

    def test_incomplete_series(self):
        self.assertEqual(series_result(sets((1, 0)), ['A', 'B'])[1], 'Em andamento')

    def test_invalid_series(self):
        for invalid in [sets((1, 1)), sets((1, 0), (2, 0), (1, 0)),
                        [dict(a='', b='', mvp=''), dict(a='2', b='1', mvp='')], sets((-1, 1))]:
            with self.subTest(sets=invalid), self.assertRaises(ValueError):
                series_result(invalid, ['A', 'B'])

    def test_both_teams_stats_and_mentions(self):
        row = dict(player='<@7>', g='3', a='2', d='9', s='1', emoji=':sillyBarou:', position='CF', sub=True)
        values = dict(time1='<@&1>', time2='<@&2>', tipo='RANKED', mvp1='<@7>', mvp3='<@8>', refs='<@10>')
        message, winner, wins = generate_extended(values, 'teste', RANKED_TEMPLATE, sets((3, 1), (4, 2), (1, 0)), [[row], [dict(row, player='<@8>')]])
        self.assertEqual((winner, wins), ('<@&1>', [3, 0]))
        for expected in ['RESULTADOS DA RANKED', 'Resultado: 3-0', '# Stats — <@&2>',
                         '**<@8> (sub)**: 3G 2A 9D 1S', '# 🏅 MVP: <@7>, <@8>', '-# hm: teste']:
            self.assertIn(expected, message)
        self.assertNotIn('{', message)

    def test_friendly_tie_and_hm(self):
        values = dict(time1='A', time2='B', placar1='2', placar2='2')
        text, winner = generate(values, 'a\n-# hm: b', '{vencedor}\n{hms}')
        self.assertEqual(winner, 'Empate')
        self.assertEqual(text, 'Empate\n-# hm: a\n-# hm: b')

    def test_stats_missing_player(self):
        with self.assertRaises(ValueError):
            stats_text([dict(player='', g='1')])

    def test_ranked_first_three_wins(self):
        for scores, expected in [(((3,1),(2,0),(1,0)),[3,0]), (((3,1),(0,1),(2,0),(1,0)),[3,1]), (((3,1),(0,1),(2,0),(0,1),(1,0)),[3,2])]:
            wins, winner, _ = series_result(sets(*scores), ['A','B'], best_of=5)
            self.assertEqual(wins, expected)
            self.assertEqual(winner, 'A')
        self.assertEqual(series_result(sets((3,1),(1,0)), ['A','B'], best_of=5)[1], 'Em andamento')
        self.assertEqual(series_result(sets((0,1),(0,2),(0,3)), ['A','B'], best_of=5)[1], 'B')
        with self.assertRaises(ValueError):
            series_result(sets((3,1),(2,0),(1,0),(2,1)), ['A','B'], best_of=5)

    def test_stale_window_does_not_erase_contacts(self):
        empty={'players':{},'roles':{}}
        saved={'players':{'Franklin':'<@7>'},'roles':{'Alpha':'<@&1>'}}
        self.assertEqual(merge_contacts(empty,empty,saved),saved)

    def test_contact_edits_preserve_other_sessions(self):
        baseline={'players':{'A':'<@1>'},'roles':{}}
        current={'players':{'A':'<@2>','B':'<@3>'},'roles':{}}
        saved={'players':{'A':'<@1>','C':'<@4>'},'roles':{'Team':'<@&5>'}}
        self.assertEqual(merge_contacts(current,baseline,saved),{'players':{'A':'<@2>','B':'<@3>','C':'<@4>'},'roles':{'Team':'<@&5>'}})
        self.assertEqual(merge_contacts({'players':{},'roles':{}},baseline,saved)['players'],{'C':'<@4>'})

    def test_per_match_totals_and_custom_rows(self):
        row=dict(player='<@7>',g='2',a='1',d='3',s='0',emoji='',position='CF',sub=False)
        matches=[[[row],[dict(row,player='<@8>',g='1')]], [[dict(row,g='4')],[]], [[],[]]]
        text,_,_=generate_extended(dict(time1='A',time2='B'),'', '{stats1}\n{partida1_stats2}\n{partida2_stats1}\n{partida4_stats1}\n{partida2_placar}',sets((3,1),(2,0),(1,0)),[[],[]],matches,'{jogador}: {g} gols, {a} assists')
        self.assertIn('<@7>: 6 gols, 2 assists',text)
        self.assertIn('<@8>: 1 gols, 1 assists',text)
        self.assertIn('<@7>: 4 gols, 1 assists',text)
        self.assertIn('2 — 0',text)
        self.assertNotIn('{',text)
        with self.assertRaises(ValueError):
            generate_extended(dict(time1='A',time2='B'),'',RANKED_TEMPLATE,sets((3,1)),[[],[]],matches)


if __name__ == '__main__':
    unittest.main()
