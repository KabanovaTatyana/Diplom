import pandas as pd
import numpy as np
import json
import xlsxwriter


def analyze_file(f, result_filename):
    try:
        try:
            data_frame = pd.read_csv(f, decimal=',', sep=';', parse_dates=[0])
        except:
            return {"error": True, "msg": "Неверный тип файла"}

        date_key = data_frame.columns[0] #'Дата'
        rate_key = data_frame.columns[1] #'Курс'
    except IndexError as e:
        return {
            'error': True, "msg": "Неверные данные"
        }

    dates = data_frame[date_key]
    rates = data_frame[rate_key]

    formats = {}
    workbook = xlsxwriter.Workbook(result_filename)
    formats['date'] = workbook.add_format({'num_format': 'DD.MM.YYYY'})
    formats['date'].set_left(6)
    formats['date'].set_right()

    formats['cell'] = workbook.add_format()

    formats['right'] = workbook.add_format()
    formats['right'].set_right()

    formats['bold'] = workbook.add_format()
    formats['bold'].set_bold()

    formats['head'] = workbook.add_format()
    formats['head'].set_bold()
    formats['head'].set_border()
    formats['head'].set_align('center')
    formats['head'].set_align('vcenter')

    worksheet_1 = workbook.add_worksheet('Лист1')
    worksheet_1.set_row(0, 20)
    worksheet_1.set_column('A:B', 12)
    worksheet_1.set_column('D:E', 12)

    worksheet_2 = workbook.add_worksheet('Лист2')

    chart = workbook.add_chart({'type': 'column'})

    H = get_Ht(dates, rates.to_numpy(), worksheet_1, formats)
    H_intrvl = get_Ht_by_intervals(dates, rates, worksheet_2, formats, chart)

    results = {
        'two' : H_intrvl,
        'one'         : {
            'H'   : H,
            'msg' : get_text_result(H)
        }
    }

    workbook.close()

    return results

def get_Ht_by_intervals(dates, rates, ws, f, chart):
    interval_data = {}
    full_data = {}

    intervals = split_time_intervals(dates, rates)

    start_row = 25
    start_column = 0

    ws.set_row(start_row, 20)

    for interval, data in intervals.items():
        _rates = data[1]
        _dates = data[0]

        A = get_colnum_string(start_column + 0)
        B = get_colnum_string(start_column + 1)
        C = get_colnum_string(start_column + 2)
        D = get_colnum_string(start_column + 3)
        F = get_colnum_string(start_column + 5)

        ws.set_column('A:%s' % F, 12)
        ws.merge_range(start_row, start_column, start_row, start_column + 5, interval, f['head'])
        ws.write(start_row+1, start_column + 0, 'Дата', f['head']) # date
        ws.write(start_row+1, start_column + 1, 'Курс',   f['head'])
        ws.write(start_row+1, start_column + 2, 'Xi-Xср1',f['head'])
        ws.write(start_row+1, start_column + 3, '',       f['head'])
        ws.merge_range(start_row+1, start_column + 4, start_row+1, start_column + 5, 'Расчет',       f['head'])


        np_rates = _rates.to_numpy()

        N = len(np_rates)

        meanVal = np.mean(np_rates)

        tmp_np_rates = np_rates.copy()
        i = 0
        data_i = _dates.index.start
        for tmp_rate in np_rates:
            row = start_row+i+2
            xi_xcp = tmp_rate - meanVal
            ws.write(row, start_column + 0, _dates[data_i+i], f['date'])
            ws.write(row, start_column + 1, tmp_rate,  f['right'])
            ws.write_formula(row, start_column + 2, '=%s%s-%s3' % (B, row+1, F), f['right'], xi_xcp)

            if i > 0:
                tmp_np_rates[i] = (xi_xcp) + tmp_np_rates[i - 1]
                ws.write_formula(row, start_column + 3, '=%s%s+%s%s' % (D, row, C, row+1), f['right'], tmp_np_rates[i])

            else:
                tmp_np_rates[i] = (xi_xcp)
                ws.write_formula(row, start_column + 3, '=%s%s' % (C, row), f['right'], tmp_np_rates[i])

            i += 1


        S = np.std(np_rates)
        R = tmp_np_rates.max() - tmp_np_rates.min()

        RS = R / S

        logRS = np.log10(RS)

        tmp = np.log10((N * np.pi) / 2)

        H = logRS / tmp

        RSt = RS / (0.998752+1.051037)

        Ht = (np.log10(RSt) / tmp) * (-0.0011 * np.log(N) + 1.0136)

        chart.add_series({
            'name':       '=Лист2!$%s$%s:$%s$%s' % (A, start_row+1, A, start_row+1),
            'values':     '=Лист2!$%s$%s' % (F, start_row+14),
        })

        last_row = start_row + N + 2
        values = {
            'Xср='         : ('=AVERAGE(%s%s:%s%s)' % (B, start_row+3, B, last_row), meanVal),
            'MAX='         : ('=MAX(%s%s:%s%s)' % (D, start_row+3, D, last_row), tmp_np_rates.max()),
            'MIN='         : ('=MIN(%s%s:%s%s)' % (D, start_row+3, D, last_row), tmp_np_rates.min()),
            'S='           : ('=STDEV(%s%s:%s%s)' % (B, start_row+3, B, last_row), S),
            'R='           : ('=%s%s-%s%s' % (F, start_row+4, F, start_row+5), R),
            'R/S='         : ('=%s%s/%s%s'  % (F, start_row+7, F, start_row+6), RS),
            'Log(R/S)='    : ('=LOG10(%s%s)'  % (F, start_row+8), logRS),
            'Log(N*pi/2)=' : ('=LOG10(%s*PI()/2)' % N, tmp),
            'Н='           : ('=%s%s/%s%s'  % (F, start_row+9, F, start_row+10), H),
            'R/St='        : ('=%s%s/(0.998752+1.051037)' % (F, start_row+8), RSt),
            'Log(R/St)='   : ('=LOG10(%s%s)' % (F, start_row+12), np.log10(RSt)),
            'Ht='          : ('=%s%s/%s%s*(-0.0011*LN(%s)+1.0136)' % (F, start_row+13, F, start_row+10, last_row), Ht)
            }

        row = start_row + 2
        for key, val in values.items():
            ws.write(row, start_column + 4, key, f['bold'])
            ws.write_formula(row, start_column + 5, val[0], f['cell'], val[1])
            row += 1


        interval_data[interval] = Ht
        full_data[interval] = {
            'H'  : Ht,
            'msg' : get_text_result(Ht)
        }

        start_column += 6

    chart.set_size({'width': 720, 'height': 480})
    chart.set_title ({'name': 'Значение константы Херста'})
    ws.insert_chart('E1', chart)

    return {
        'labels' : list(interval_data.keys()),
        'data'   : list(interval_data.values()),
        'full_data' : full_data
    }


def split_time_intervals(dates, rates):
    intervals = {}

    years = pd.DatetimeIndex(dates).year
    years_uniq = years.unique()

    delta = ((((years_uniq.max() - years_uniq.min()) / 10 - 1) // 1) * 10) + (years_uniq.max() - years_uniq.min()) % 10 + 1

    for i in range(10):

        start = years.searchsorted(years_uniq[i])
        try:
            end = years.searchsorted(years_uniq[i + delta + 1])
        except IndexError as e:
            end = len(years)

        intervals['%s-%s' % (years_uniq[i], years_uniq[i + delta])] = (dates[start:end], rates[start:end])

    return intervals


def get_Ht(dates, rates, ws, f):
    ws.write('A1', 'data', f['head'])
    ws.write('B1', 'curs', f['head'])

    average = sum([rate for rate in rates]) / len(rates)

    d_column = 0
    d_column_vals = []

    for i, date in enumerate(dates):
        ws.write('A%s' % (i+2), date, f['date'])
        ws.write('B%s' % (i+2), rates[i])
        ws.write('C%s' % (i+2), rates[i] - average)
        d_column += (rates[i] - average)
        d_column_vals.append(d_column)
        ws.write('D%s' % (i+2), d_column)

    d_column_vals = pd.DataFrame(d_column_vals)

    N = len(rates)

    meanVal = np.mean(rates)
    S = np.std(rates)
    R = float(d_column_vals.max() - d_column_vals.min())
    RS = R / S
    log10R = np.log10(RS)

    tmp = np.log10((N * np.pi) / 2)

    H = log10R / tmp

    RSt = RS / (0.998752+1.051037)

    Ht = (np.log10(RSt) / tmp) * (-0.0011 * np.log(N) + 1.0136)
    values = {
        'Xср='         : ('=AVERAGE(B2:B%s)' % (N + 1), meanVal),
        'MAX='         : ('=MAX(D2:D%s)' % (N + 1), d_column_vals.max()),
        'MIN='         : ('=MIN(D2:D%s)' % (N + 1), d_column_vals.min()),
        'S='           : ('=STDEV(B2:B%s)' % (N + 1), S),
        'R='           : ('=I3-I4', R),
        'R/S='         : ('=I6/I5', RS),
        'Log(R/S)='    : ('=LOG10(I7)', log10R),
        'Log(n*pi/2)=' : ('=LOG10(%s*PI()/2)' % (N), tmp),
        'Н='           : ('=I8/I9', H),
        'R/St='        : ('=I7/(0.998752+1.051037)', RSt),
        'Log(R/St)='   : ('=LOG10(I11)', np.log10(RSt)),
        'Ht='          : ('=I12/I9*(-0.0011*LN(%s)+1.0136)' % (N), Ht)
        }

    row = 2
    for key, val in values.items():
        ws.write('H%s' % row, key)
        ws.write_formula('I%s' % row, val[0])
        row += 1

    return Ht

def get_colnum_string(n):
    n += 1
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

def get_text_result(H):
    return {
        H == 0                  : 'Рынок «мертвый», никаких движений или они цикличны с очень большой частотой колебаний.',
        0 <= H < 0.5            : 'Рынок стремится возвратиться к среднему значению. Ряд неустойчив. Чем Н ближе к 0, тем неустойчивей динамика цен (за подъемом следует спад и наоборот).',
        H == 0.5                : 'Ряд абсолютно случайный, события не зависят друг от друга.',
        0.326 <= H <= 0.674     : 'Ряд с высокой вероятностью случайный. События, скорее всего, не зависят друг от друга.',
        np.around(H, 2) == 0.72 : 'Эмпирическое значение показателя Херста для природных явлений.',
        0.85 < H < 0.87         : 'К этому значению стремится линейный (растущий или нисходящий) тренд при сравнительно больших n (до 5000).',
        0.5 < H <= 1            : 'Трендоустойчивый (персистентный) рынок. Чем Н ближе к 1, тем сильнее тренд (за подъемом наверняка последует подъем, а за спадом – спад). Рынок обладает долговременной памятью – будущее зависит от прошлого.',
        H > 1                   : 'Очень редкое явление. Возникают независимые скачки амплитуды, распределенные по Леви.'
    }[True]
