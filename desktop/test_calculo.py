"""Testes da lógica de cálculo do Mapa de Carga Horária."""

import unittest

from calculo import calcular, periodo_meses, chave, anos_do_periodo


def ch_uniforme(mes_final_ano, mes_final_mes, n, valor):
    return {chave(a, m): valor for a, m in periodo_meses(mes_final_ano, mes_final_mes, n)}


class TestPeriodo(unittest.TestCase):
    def test_quantidade_e_ordem(self):
        meses = periodo_meses(2026, 5, 60)  # junho/2026, 0-based mes=5
        self.assertEqual(len(meses), 60)
        self.assertEqual(meses[-1], (2026, 5))          # último = mais recente
        self.assertEqual(meses[0], (2021, 6))           # 60 meses antes
        self.assertTrue(meses[0] < meses[-1])

    def test_anos(self):
        meses = periodo_meses(2026, 5, 60)
        self.assertEqual(anos_do_periodo(meses), [2021, 2022, 2023, 2024, 2025, 2026])


class TestCalculo(unittest.TestCase):
    def test_titular_media_maior_que_jornada(self):
        # 60 meses a 180h, jornada básica 150 -> média 180, suplementar 30
        ch = ch_uniforme(2026, 5, 60, 180)
        r = calcular(ch, "titular", 150, 60, 2026, 5)
        self.assertEqual(r.total, 180 * 60)
        self.assertEqual(r.media, 180)
        self.assertEqual(r.tipo_quadro, "completo")
        self.assertEqual(r.jornada, 150)
        self.assertEqual(r.suplementar, 30)

    def test_titular_media_menor_que_jornada(self):
        # média 150 < jornada completa 200 -> apenas 1º quadro
        ch = ch_uniforme(2026, 5, 60, 150)
        r = calcular(ch, "titular", 200, 60, 2026, 5)
        self.assertEqual(r.media, 150)
        self.assertEqual(r.tipo_quadro, "unico")
        self.assertEqual(r.suplementar, 0)

    def test_titular_media_igual_jornada(self):
        ch = ch_uniforme(2026, 5, 60, 200)
        r = calcular(ch, "titular", 200, 60, 2026, 5)
        self.assertEqual(r.media, 200)
        self.assertEqual(r.tipo_quadro, "completo")
        self.assertEqual(r.suplementar, 0)

    def test_ofa_sempre_unico(self):
        # OFA com média 180 > jornada -> ainda assim só o 1º quadro
        ch = ch_uniforme(2026, 5, 60, 180)
        r = calcular(ch, "ofa", 150, 60, 2026, 5)
        self.assertEqual(r.media, 180)
        self.assertEqual(r.tipo_quadro, "unico")

    def test_arredondamento(self):
        # total 9900 em 60 meses -> 165 exato; testar fração
        ch = ch_uniforme(2026, 5, 60, 150)
        # ajusta um mês para gerar fração: total 9000+...
        primeiro = chave(*periodo_meses(2026, 5, 60)[0])
        ch[primeiro] = 175  # total = 150*59 + 175 = 9025 -> /60 = 150.41... -> 150
        r = calcular(ch, "titular", 150, 60, 2026, 5)
        self.assertEqual(r.total, 9025)
        self.assertEqual(r.media, round(9025 / 60))
        self.assertEqual(r.media, 150)

    def test_periodo_84(self):
        ch = ch_uniforme(2026, 5, 84, 160)
        r = calcular(ch, "titular", 150, 84, 2026, 5)
        self.assertEqual(r.n_meses, 84)
        self.assertEqual(r.total, 160 * 84)
        self.assertEqual(r.media, 160)
        self.assertEqual(r.suplementar, 10)

    def test_meses_vazios_contam_como_zero(self):
        r = calcular({}, "titular", 150, 60, 2026, 5)
        self.assertEqual(r.total, 0)
        self.assertEqual(r.media, 0)
        self.assertEqual(r.tipo_quadro, "unico")  # 0 < 150

    def test_totais_anuais(self):
        ch = ch_uniforme(2026, 5, 60, 100)
        r = calcular(ch, "titular", 150, 60, 2026, 5)
        # 2021 tem meses jul-dez = 6 meses; 2026 tem jan-jun = 6 meses
        self.assertEqual(r.totais_anuais[2021], 600)
        self.assertEqual(r.totais_anuais[2026], 600)
        self.assertEqual(r.totais_anuais[2022], 1200)  # 12 meses


if __name__ == "__main__":
    unittest.main(verbosity=2)
