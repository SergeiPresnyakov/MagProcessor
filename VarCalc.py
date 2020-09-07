import datetime as dt

class MagProcessor:
    def __init__(self, address: str):
        self.address = address
        self.data_set = {}
    
    def create_data_set(self, mode: str):
        self.mode = mode
        with open(self.address) as file:
            content = file.readlines()
            content = [line.strip().split('\t') for line in content][8:]

            # Создание набора данных. Ключ - время измерения
            if self.mode == 'variation':
                self.variation_interval = int(input('Интервал вариаций (сек): '))
                self.data_set = {row[2]: {'diap': row[1], 'field': float(row[0]), 'time': row[2]} for row in content}
                print('[v] Данные вариации готовы к обработке')
            elif mode == 'measurements':
                self.data_set = {row[2]: {'field': float(row[0]), 'diap': row[1], 'time': row[2], 'pr': row[3], 'pk': row[4]} for row in content}
                print('[v] Данные рядовых измерений готовы к обработке')
            else:
                print('[!] Unknown mode. Expected "variation" or "measurements"')

    def __str__(self):
        for element in sorted(self.data_set.values(), key=lambda x: x['time']):
            print(element)
        return ''

    def split_to_pairs(self, el):
        return [(el[i], el[i+1]) for i in range(len(el) - 1)]
    
    def even_time(self, pair):
        """Получает пару строк формата чч:мм:сс. Вычисляет среднее время
        и возвращает строку времени в том же формате
        """
        buffer = []
        for el in pair:
            el = list(map(int, el.split(':')))
            sec = (el[0]*3600) + (el[1]*60) + (el[2])
            buffer.append(sec)

        avg_time = str(dt.timedelta(seconds=(sum(buffer) / 2)))
        if len(avg_time) == 7:
            avg_time = '0' + avg_time
        return avg_time

    def get_interpolation_times(self):
        seconds = self.variation_interval
        times = 0
        while seconds % 2 == 0:
            seconds //= 2
            times += 1
        return times

    def interpolate_data(self):
        self.times = self.get_interpolation_times()
        if self.mode == 'variation':
            for _ in range(self.times):
                self.variation_interval /= 2
                self.pairs = self.split_to_pairs([row['time'] for row in sorted(self.data_set.values(), key=lambda x: x['time'])])
                for pair in self.pairs:
                    self.data_set[self.even_time(pair)] = {'diap': '0', 'field': round((self.data_set[pair[0]]['field'] + \
                        self.data_set[pair[1]]['field']) / 2, 2), 'time': self.even_time(pair)}
        else:
            print('[!] Интерполяция времени доступна только для вариаций (режим variation)')
    
    def closest_time(self, time_, interval):
        """Получает строку со временем в формате чч:мм:сс. Округляет время вниз до ближайших variation_interval
        Возвращает новую строку в этом же формате
        """
        time_ = list(map(int, time_.split(':')))
        sec = (time_[0]*3600) + (time_[1]*60) + (time_[2])
        sec -= sec % interval

        result = str(dt.timedelta(seconds=sec))
        if len(result) == 7:
            result = '0' + result
        return result
    
    # в экземпляр с рядовыми измерениями
    # передаём экземпляр с вариацией
    # не наоборот!
    def calculate_dT(self, v):
        """Значение dT = разность измеренного поля и вариации в этот момент"""
        for time in self.data_set:
            self.data_set[time]['var'] = v.data_set[self.closest_time(time, v.variation_interval)]['field']
            self.data_set[time]['dT'] = round(self.data_set[time]['field'] - self.data_set[time]['var'], 2)

    def write_to_file(self, name):
        """Записывает data_set в файл"""

        # что можно преобразуем в строки, добавляем 0 в конец значения field где надо, чтобы было 2 знака после запятой
        self.data_set = self.data_set.values()
        for element in self.data_set:
            element['field'] = str(element['field'])
            element['dT'] = str(element['dT'])
            element['var'] = str(element['var'])

            if len(element['field']) == 7:
                element['field'] = element['field'] + '0'

        with open(name, 'w') as output:
            output.write('Field\tD\tTime\tPr\tPk\tVariation\tdT\n')
            for line in sorted(self.data_set, key=lambda x: (x['pr'], x['pk'])):
                output.write(f"{line['field']}\t{line['diap']}\t{line['time']}\t{line['pr']}\t{line['pk']}\t{line['var']}\t{line['dT']}\n")
        print('[v] Файл записан')


def main():
    print('''
Расчёт вариации v1.2
----------------------
Чтобы расчитать dT введите имя рабочей папки, а также
имена файлов с вариацией и магниткой.
----------------------''')
    folder = input('Рабочая папка: ')
    var_name = input('Файл с вариацией: ')        
    var = MagProcessor(f'{folder}\\{var_name}')
    var.create_data_set('variation')
    var.interpolate_data()  # при интервале вариаций 120 секунд times=2 - интервал 30 сек, times=3 - интервал 15 секунд

    mag_name = input('Файл с рядовыми измерениями: ')
    mag = MagProcessor(f'{folder}\\{mag_name}')
    mag.create_data_set('measurements')
    mag.calculate_dT(var)
    mag.write_to_file(f'{folder}\\{mag_name[:-4]} с поправками на вариацию.txt')


if __name__ == "__main__":
    main()
