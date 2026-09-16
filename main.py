import flet as ft
import json
import os


class SalaryCalculator:
    W, N, NR, ND, DH, NH = 300, 230, 0.4, 0.13, 11, 7

    def __init__(self, t, d, n, hd, hn, rg, nr, pr, cp, av):
        self.t, self.d, self.n, self.hd, self.hn = map(float, (t, d, n, hd, hn))
        self.rc, self.nc, self.pr = float(rg) / 100, float(nr) / 100, float(pr) / 100
        self.cp, self.av = float(cp), float(av)

    def calculate(self):
        R9 = self.d * self.DH * self.t
        R8 = self.d * self.W
        R13 = self.n * self.NH * self.t * self.NR
        R19 = self.hd * self.DH * self.t
        R20 = self.t * self.hn * 7
        R21 = self.t * self.hn * 4
        R11 = (R9 + R19 + R20 + R21) * self.pr
        R17 = self.d * self.N
        base = R9 + R11 + R13 + R19 + R20 + R21
        R14, R16 = base * self.rc, base * self.nc
        R7 = R8 + base + R14 + R16 + R17 + self.cp
        nd = (R7 - R8 - self.cp) * self.ND
        r = lambda x: round(x, 2)
        return {
            'Оплата по тарифу': r(R9), 'Вахтовая надбавка': r(R8),
            'Ночная доплата': r(R13), 'Праздничные дневные': r(R19),
            'Праздничные ночные (ночь)': r(R20), 'Праздничные ночные (день)': r(R21),
            'Премия': r(R11), 'Питание': r(R17),
            'Районный коэффициент': r(R14), 'Северная надбавка': r(R16),
            'Компенсация проезда': r(self.cp),
            'Итого начислено': r(R7), 'НДФЛ': r(nd),
            'К выплате': r(R7 - round(nd) - self.av),
        }


STEPS = (
    ('tariff', 'Тарифная ставка (за час)', 'n'),
    ('days', 'Отработано дней', 'n'),
    ('night_shifts', 'Ночных смен', 'n'),
    ('holiday_day', 'Праздничных дневных смен', 'n'),
    ('holiday_night', 'Праздничных ночных смен', 'n'),
    ('regional', 'Районный коэффициент (%)', 'n'),
    ('northern', 'Северная надбавка (%)', 'n'),
    ('premium', 'Премия (%)', 'n'),
    ('comp_received', 'Получали ли вы уже оплату компенсации за проезд?', 'yn'),
    ('compensation', 'Сумма компенсации за проезд', 'n'),
    ('advance', 'Аванс', 'n'),
)
DEFAULTS = {'tariff': '139.83', 'days': '31', 'night_shifts': '16', 'holiday_day': '0',
            'holiday_night': '0', 'regional': '80', 'northern': '80', 'premium': '40',
            'comp_received': 'Нет', 'compensation': '0', 'advance': '0'}

_storage = os.getenv("FLET_APP_STORAGE_DATA") or os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(_storage, 'nnk_buh.json')


def load():
    try:
        with open(CONFIG, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        d = DEFAULTS.copy()
        d.update({k: str(v) for k, v in saved.items() if k in DEFAULTS})
        return d
    except Exception:
        return DEFAULTS.copy()


def store(d):
    try:
        os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
        with open(CONFIG, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def main(page: ft.Page):
    page.title = "ННКБух"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO

    data = load()
    state = {'i': 0}

    title = ft.Text(size=20, weight=ft.FontWeight.BOLD)
    num = ft.TextField(width=280, keyboard_type=ft.KeyboardType.NUMBER)
    yn = ft.RadioGroup(content=ft.Row(
        [ft.Radio(value="Да", label="Да"), ft.Radio(value="Нет", label="Нет")],
        alignment=ft.MainAxisAlignment.CENTER))
    box = ft.Container(alignment=ft.Alignment.CENTER)
    back = ft.ElevatedButton("Назад", on_click=lambda e: nav(-1), disabled=True)
    nxt = ft.ElevatedButton("Далее", on_click=lambda e: nav(1))
    rst = ft.ElevatedButton("В начало", on_click=lambda e: restart(), visible=False)
    res = ft.Text(selectable=True, size=16, visible=False)

    def on_num_change(e):
        i = state['i']
        if 0 <= i < len(STEPS):
            key, _, kind = STEPS[i]
            if kind != 'yn':
                data[key] = (num.value or '').strip()
                store(data)

    def on_yn_change(e):
        data['comp_received'] = yn.value or 'Нет'
        store(data)

    num.on_change = on_num_change
    yn.on_change = on_yn_change

    def visible(i):
        return 0 <= i < len(STEPS) and (STEPS[i][0] != 'compensation' or data['comp_received'] == 'Нет')

    def find(i, d):
        i += d
        while 0 <= i < len(STEPS) and not visible(i):
            i += d
        return i

    def render():
        i = state['i']
        if i >= len(STEPS):
            show_result()
            return
        key, label, kind = STEPS[i]
        title.value = f"Шаг {i + 1}/{len(STEPS)}: {label}"
        if kind == 'yn':
            yn.value = data['comp_received']
            box.content = yn
        else:
            num.value, num.label = data[key], label
            box.content = num
        back.disabled = find(i, -1) < 0
        nxt.text = "Рассчитать" if find(i, 1) >= len(STEPS) else "Далее"
        box.visible = back.visible = nxt.visible = True
        res.visible = rst.visible = False
        page.update()

    def save():
        i = state['i']
        if 0 <= i < len(STEPS):
            key, _, kind = STEPS[i]
            if kind == 'yn':
                data['comp_received'] = yn.value or 'Нет'
            else:
                data[key] = (num.value or '').strip()

    def nav(d):
        save()
        store(data)
        ni = find(state['i'], d)
        state['i'] = ni if ni >= 0 else 0
        render()

    def show_result():
        try:
            if data['comp_received'] == 'Да':
                data['compensation'] = '0'
            f = lambda k: data[k].replace(',', '.')
            r = SalaryCalculator(f('tariff'), f('days'), f('night_shifts'), f('holiday_day'),
                                 f('holiday_night'), f('regional'), f('northern'),
                                 f('premium'), f('compensation'), f('advance')).calculate()
            title.value = "Результат расчёта"
            res.value = "\n".join(f"{k}: {v}" for k, v in r.items())
        except Exception as ex:
            title.value = "Ошибка"
            res.value = f"Ошибка: {ex}"
        store(data)
        box.visible = back.visible = nxt.visible = False
        res.visible = rst.visible = True
        page.update()

    def restart():
        nonlocal data
        data = DEFAULTS.copy()
        store(data)
        state['i'] = 0
        render()

    page.add(ft.Column([
        title, box,
        ft.Row([back, nxt], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        rst, res,
    ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    render()


ft.run(main)
