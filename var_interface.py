import tkinter as tk
from tkinter import filedialog as fd
from VarCalc import MagProcessor


class GUIMagProcessor(MagProcessor):
    def __init__(self, address):
        self.mode = ''
        self.variation_interval = 0
        self.data_set = {}
        MagProcessor.__init__(self, address)

    def create_data_set(self, mode, app):
        self.mode = mode
        with open(self.address, encoding='cp1251') as file:
            content = file.readlines()
            content = [line.strip().split('\t') for line in content][8:]

            # Создание набора данных. Ключ - время измерения
            if self.mode == 'variation':
                self.variation_interval = int(app.var_interval.get())
                self.data_set = {
                    row[2]: {
                        'diap': row[1],
                        'field': float(row[0]),
                        'time': row[2]
                    } for row in content
                }
            elif mode == 'measurements':
                self.data_set = {
                    row[2]: {
                        'field': float(row[0]),
                        'diap': row[1],
                        'time': row[2],
                        'pr': row[3],
                        'pk': row[4]
                    } for row in content
                }


class Window:
    def __init__(self, parent):
        parent.geometry('1000x400')
        parent.title('Расчёт вариаций')
        parent.resizable(False, False)
        self.meas_address = ''
        self.var_address = ''
        self.open_meas_button = tk.Button(parent, text='Рядовые измерения', font='calibri 18', width=17)
        self.open_var_button = tk.Button(parent, text='Вариации', font='calibri 18', width=17)
        self.meas_address_field = tk.Label(parent, width=60, font='calibri 18', bg='gray')
        self.var_address_field = tk.Label(parent, width=60, font='calibri 18', bg='gray')
        self.var_interval = tk.Entry(parent, width=4, font='calibri 18')
        self.calc_button = tk.Button(parent, text='Посчитать', font='calibri 18')

        self.open_meas_button.place(relx=0.03, rely=0.05, anchor='nw')
        self.meas_address_field.place(relx=0.25, rely=0.07, anchor='nw')
        self.open_var_button.place(relx=0.03, rely=0.2, anchor='nw')
        self.var_address_field.place(relx=0.25, rely=0.22, anchor='nw')
        self.var_interval.place(relx=0.03, rely=0.35, anchor='nw')
        self.calc_button.place(relx=0.5, rely=0.5, anchor='n')
        tk.Label(parent, text='Интервал вариаций, сек', font='calibri 15').place(relx=0.09, rely=0.35)

        self.open_meas_button['command'] = self.get_meas_address
        self.open_var_button['command'] = self.get_var_address
        self.calc_button['command'] = self.calculate

    def get_meas_address(self):
        self.meas_address = fd.askopenfilename()
        self.meas_address_field.config(text=self.meas_address)

    def get_var_address(self):
        self.var_address = fd.askopenfilename()
        self.var_address_field.config(text=self.var_address)

    def calculate(self):
        var = GUIMagProcessor(self.var_address)
        var.create_data_set('variation', self)
        var.interpolate_data(times=3)

        mag = GUIMagProcessor(self.meas_address)
        mag.create_data_set('measurements', self)
        mag.calculate_dT(var)
        mag.write_to_file(f'{self.meas_address[:-4]} с поправками на вариацию.txt')


def main():
    root = tk.Tk()
    Window(root)
    root.mainloop()


if __name__ == "__main__":
    main()
