import sys
import numpy as np
import rasterio
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPalette, QBrush, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from form_of_window import Form1
import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox


def decimal_to_dms(degrees):
    """Преобразует десятичные градусы в градусы, минуты и секунды."""
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = (degrees - d - m / 60) * 3600
    return d, m, round(s, 2)  # Округляем секунды до двух знаков после запятой

#Данный метод учитывает кривизну земной поверхности, что позволяет рассчитать геодезическое расстояние
#между двумя точками, что является более точным.
def haversine(coord1, coord2):
    R = 6371e3  # Радиус Земли в метрах
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    distance = R * c  # Расстояние в метрах
    return distance

#Основной класс программы
class Form_main(QtWidgets.QMainWindow,Form1):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.selected_points = []

        self.colorbar = None
        # Создание вертикального layout для виджета map
        layout = QVBoxLayout(self.map)

        # Создание canvas
        self.canvas = FigureCanvas(plt.Figure())
        layout.addWidget(self.canvas)

        # Настройка subplot
        self.ax = self.canvas.figure.add_subplot(111)

        self.height_of_base_station_1 = 0
        self.height_of_base_station_2 = 0

        # Связываем нажатие кнопки с методом open_file_dialog для дальнейшей работы
        self.pushButton_load_map.clicked.connect(self.open_file_dialog)
        # Связываем нажатие кнопки ввода высот базовых станций с методом обработки
        self.pushButton_input_values_height_base_station.clicked.connect(self.add_height_of_base_station)
        # Связываем нажатие кнопки отображения профиля высот с соответствующим методом
        self.pushButton_show_graphic.clicked.connect(self.show_prof)
        # Связываем нажатие кнопки очистки значений с соответствующим методом
        self.pushButton_clean_values.clicked.connect(self.clear_values)
        # Связываем нажатие кнопки установки на карте точки 1 с соответствующим методом
        self.pushButton_set_map_point1.clicked.connect(self.prepare_point1_selection)
        # Связываем нажатие кнопки установки на карте точки 2 с соответствующим методом
        self.pushButton_set_map_point2.clicked.connect(self.prepare_point2_selection)
        # Связываем нажатие кнопки ручной установки на карте точек  с соответствующим методом
        self.pushButton_set_point_on_map.clicked.connect(self.set_points)

        #Устанавливаем блокировку на кнопки до момента загрузки карты в программе
        self.pushButton_set_point_on_map.setEnabled(False)
        self.pushButton_set_map_point1.setEnabled(False)
        self.pushButton_set_map_point2.setEnabled(False)
        self.pushButton_input_values_height_base_station.setEnabled(False)
        self.pushButton_show_graphic.setEnabled(False)
        self.pushButton_clean_values.setEnabled(False)
        self.pushButton_input_values_height_base_station.setEnabled(False)


    # Метод предоставляет возможность выбора необходимой карты формата .hgt
    def open_file_dialog(self):
        if len(self.selected_points)>0:
            QMessageBox.warning(self, "ВНИМАНИЕ", "Перед загрузкой другой карты необходимо провести очистку значений.")
        else:
            # Open the file dialog
            options = QFileDialog.Options()
            self.file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "",
                                                       "Все файлы (*.*);;Текстовые файлы (*.txt);;Изображения (*.png *.jpg);;HGT файлы (*.hgt)",
                                                       options=options)
            # Проверяем, что файл выбран
            if self.file_path:
                # Проверяем, существует ли файл
                if os.path.isfile(self.file_path):
                    # Проверяем, является ли файл формата .hgt
                    if self.file_path.endswith('.hgt'):
                        self.plot_elevation_map()  # Если все правильно, то запускаем метод отображения карты
                    else:
                        QMessageBox.warning(self, "Неверный формат", "Выбранный файл не является файлом формата .hgt.")
                else:
                    QMessageBox.warning(self, "Ошибка", "Файл не существует.")
            self.pushButton_clean_values.setEnabled(False)
            self.pushButton_set_point_on_map.setEnabled(True)
            self.pushButton_set_map_point1.setEnabled(True)
            self.pushButton_set_map_point2.setEnabled(True)
            self.pushButton_input_values_height_base_station.setEnabled(True)
            self.pushButton_show_graphic.setEnabled(True)
            self.pushButton_clean_values.setEnabled(True)
            #Устанавливаем блокировку на кнопку постановки второй точки, для корректной работы программы.
            self.pushButton_set_map_point2.setEnabled(False)

    # Метод проверяет, что выбрана первая точка(нужно чтобы ограничить число выбираемых точек)
    def prepare_point1_selection(self):
        """Подготовка к выбору первой точки"""
        if len(self.selected_points) == 0:
            self.pushButton_set_map_point1.setEnabled(False)
            self.pushButton_set_map_point2.setEnabled(True)
            self.canvas.mpl_connect('button_press_event', self.onclick_point1)

    # Метод проверяет, что выбрана вторая точка(нужно чтобы ограничить число выбираемых точек)
    def prepare_point2_selection(self):
        """Подготовка к выбору второй точки"""
        if len(self.selected_points) == 1:
            self.pushButton_set_map_point2.setEnabled(False)
            self.canvas.mpl_connect('button_press_event', self.onclick_point2)

    # Метод установки на карте точке номер 1
    def onclick_point1(self, event):
        #Ставим блокировку на кнопку ввода высот, после нажатия кнопки установки первой станции.
        self.pushButton_input_values_height_base_station.setEnabled(False)
        self.pushButton_set_point_on_map.setEnabled(False)
        self.pushButton_clean_values.setEnabled(True)
        self.pushButton_load_map.setEnabled(False)
        #Разблокируем кнопку установки точки номер 2.
        self.pushButton_set_map_point2.setEnabled(True)
        """Обработчик клика для первой точки"""
        if event.xdata is not None and event.ydata is not None:
            lon_index = int(event.xdata)
            lat_index = int(event.ydata)
            lon = self.bounds.left + (lon_index / self.width) * (self.bounds.right - self.bounds.left)
            lat = self.bounds.top - (lat_index / self.height) * (self.bounds.top - self.bounds.bottom)

            self.selected_points.append((round(lat, 4), round(lon, 4)))

            # Отмечаем первую точку
            self.ax.plot(event.xdata, event.ydata, 'ro')
            self.ax.text(event.xdata + 10, event.ydata + 10,
                         f'Точка 1: {self.selected_points[-1]}',
                         color='white', fontsize=10)

            self.canvas.draw()
            self.canvas.mpl_disconnect(self.canvas.mpl_connect('button_press_event', self.onclick_point1))

    # Метод установки на карте точке номер 2
    def onclick_point2(self, event):
        self.pushButton_set_point_on_map.setEnabled(False)
        self.pushButton_clean_values.setEnabled(True)
        self.pushButton_load_map.setEnabled(False)
        """Обработчик клика для второй точки"""
        if event.xdata is not None and event.ydata is not None:
            lon_index = int(event.xdata)
            lat_index = int(event.ydata)
            lon = self.bounds.left + (lon_index / self.width) * (self.bounds.right - self.bounds.left)
            lat = self.bounds.top - (lat_index / self.height) * (self.bounds.top - self.bounds.bottom)

            self.selected_points.append((round(lat, 4), round(lon, 4)))

            # Отмечаем вторую точку
            self.ax.plot(event.xdata, event.ydata, 'ro')
            self.ax.text(event.xdata + 10, event.ydata + 10,
                         f'Точка 2: {self.selected_points[-1]}',
                         color='white', fontsize=10)

            self.canvas.draw()
            self.canvas.mpl_disconnect(self.canvas.mpl_connect('button_press_event', self.onclick_point2))

    # Метод считывает значения высот базовых станция и проверяет их на корректность
    def add_height_of_base_station(self):
        # Считываем значение высоты для первой станции
        self.height_of_base_station_1 = self.spinBox_height_of_basestation_1.value()
        # Считываем значение высоты для первой станции
        self.height_of_base_station_2 = self.spinBox_height_of_basestation_2.value()
        # Проверяем значение на корректность
        if self.height_of_base_station_2 > 40 or self.height_of_base_station_1 > 40:
            QMessageBox.warning(self, "ВНИМАНИЕ","Введенное вами значение высоты либо слишком большое.Оно не должно превышать 40.Измените его!")
            self.pushButton_input_values_height_base_station.setEnabled(True)
            self.pushButton_show_graphic.setEnabled(False)
            self.pushButton_clean_values.setEnabled(False)
            self.height_of_base_station_1 = 0
            self.height_of_base_station_2 = 0
        else:
            self.pushButton_input_values_height_base_station.setEnabled(False)
            self.pushButton_show_graphic.setEnabled(True)
            self.pushButton_clean_values.setEnabled(True)

    # Метод отображения профиля местности между двумя точками.
    def show_profile(self):
        self.pushButton_clean_values.setEnabled(True)
        self.pushButton_load_map.setEnabled(True)
        """Отображение профиля местности между двумя выбранными точками."""
        plt.close('all')

        if len(self.selected_points) == 2:
            lat1, lon1 = self.selected_points[0]
            lat2, lon2 = self.selected_points[1]

            x1 = int((lon1 - self.bounds.left) / (self.bounds.right - self.bounds.left) * self.width)
            y1 = int((self.bounds.top - lat1) / (self.bounds.top - self.bounds.bottom) * self.height)

            x2 = int((lon2 - self.bounds.left) / (self.bounds.right - self.bounds.left) * self.width)
            y2 = int((self.bounds.top - lat2) / (self.bounds.top - self.bounds.bottom) * self.height)

            num_points = max(abs(x2 - x1), abs(y2 - y1)) + 1

            lons_interp = np.linspace(lon1, lon2, num_points)
            lats_interp = np.linspace(lat1, lat2, num_points)

            elevations = []

            for lon, lat in zip(lons_interp, lats_interp):
                x_index = int((lon - self.bounds.left) / (self.bounds.right - self.bounds.left) * self.width)
                y_index = int((self.bounds.top - lat) / (self.bounds.top - self.bounds.bottom) * self.height)
                elevations.append(self.elevation_data[y_index, x_index])

            # Динамический расчет радиуса зоны Френеля
            distance_meters = haversine(self.selected_points[0], self.selected_points[1])
            frequency = 2.4  # Пример частоты в ГГц (WiFi)

            # Формула расчета радиуса зоны Френеля
            radius_fresnel_1st_zone_meters = 17.31 * np.sqrt(
                (distance_meters / 1000) / (4 * frequency)
            )

            print(f"Радиус первой зоны Френеля: {radius_fresnel_1st_zone_meters:.2f} метров")

            # Генерация синусоидальной верхней границы эллипса относительно зеленой линии
            linear_elevation_line = np.linspace(elevations[0] + self.height_of_base_station_1,
                                                elevations[-1] + self.height_of_base_station_2, num_points)
            sinusoidal_variation = radius_fresnel_1st_zone_meters * np.sin(np.linspace(0, np.pi, num_points))
            ellipse_y_upper = linear_elevation_line + sinusoidal_variation

            # Расчет расстояния между точками
            distance_meters = haversine(self.selected_points[0], self.selected_points[1])
            distance_kilometers = distance_meters / 1000.0

            profile_fig, profile_ax = plt.subplots(figsize=(10, 5))

            # Построение профиля местности
            x_kilometers = np.linspace(0, distance_kilometers, num_points)

            # Рассчитываем кривизну Земли для каждой точки
            R = 6371000  # Радиус Земли в метрах
            x_meters = np.linspace(-distance_meters / 2, distance_meters / 2, num_points)  # Расстояние от центра
            y_curvature = -(x_meters ** 2) / (2 * R) + (distance_meters ** 2) / (8 * R)  # Формула для кривизны Земли

            # Складываем высоты рельефа с кривизной Земли
            elevations_with_curvature = elevations + y_curvature

            # Построение профиля без учёта кривизны Земли (менее яркий и пунктирный)
            profile_ax.plot(x_kilometers, elevations,
                            color='blue', linestyle='--', alpha=0.7, label='Профиль рельефа (без кривизны Земли)')

            # Построение профиля с учётом кривизны Земли
            profile_ax.plot(x_kilometers, elevations_with_curvature,
                            color='brown', linestyle='-', label='Профиль рельефа (с кривизной Земли)')

            # Построение кривизны Земли (визуализация поверхности Земли)
            profile_ax.plot(x_kilometers, y_curvature,  # Используем y_curvature вместо -y_curvature
                            color='purple', linestyle='--', label='Кривизна Земли (поверхность)')

            # Построение верхней границы эллипса
            profile_ax.plot(np.linspace(0, distance_kilometers, num_points), ellipse_y_upper,
                            color='yellow', linestyle='-', label='Верхняя граница зоны Френеля')

            # Находим максимальное значение кривизны
            max_curvature = np.max(y_curvature)
            max_curvature_index = np.argmax(y_curvature)
            max_curvature_x = x_kilometers[max_curvature_index]

            # Отображаем максимальное значение кривизны на графике
            profile_ax.annotate(f'Макс. кривизна: {max_curvature:.2f} м',
                                xy=(max_curvature_x, max_curvature),
                                xytext=(max_curvature_x, max_curvature + 10),
                                arrowprops=dict(facecolor='black', shrink=0.05),
                                fontsize=10, color='black')

            # Добавление прямых линий для высот базовых станций
            profile_ax.plot([0, 0], [elevations[0], elevations[0] + self.height_of_base_station_1],
                            color='red', linestyle='-', label='Высота базовой станции 1')
            profile_ax.plot([distance_kilometers, distance_kilometers],
                            [elevations[-1], elevations[-1] + self.height_of_base_station_2],
                            color='red', linestyle='-', label='Высота базовой станции 2')

            # Добавление зеленой линии между вершинами прямых линий
            profile_ax.plot([0, distance_kilometers], [elevations[0] + self.height_of_base_station_1,
                                                       elevations[-1] + self.height_of_base_station_2],
                            color='green', linestyle='--', label='Линия между базовыми станциями')

            # Отображение расстояния между точками (длина зеленой линии)
            mid_x = distance_kilometers / 2  # Середина профиля по оси X
            mid_y = (elevations[0] + self.height_of_base_station_1 + elevations[
                -1] + self.height_of_base_station_2) / 2  # Середина по оси Y
            profile_ax.annotate(f'Расстояние: {distance_kilometers:.2f} км',
                                xy=(mid_x, mid_y),
                                xytext=(mid_x, mid_y + 20),  # Смещение текста выше середины
                                fontsize=10, color='green',
                                bbox=dict(facecolor='white', alpha=0.8, edgecolor='green'))

            # Проведение вертикальных линий из точек 1 и 2 до высоты 0
            profile_ax.plot([0, 0], [0, elevations[0]], color='black', linestyle=':',
                            label='Вертикальная линия до 0 (Точка 1)')
            profile_ax.plot([distance_kilometers, distance_kilometers], [0, elevations[-1]],
                            color='black', linestyle=':', label='Вертикальная линия до 0 (Точка 2)')

            # Проведение горизонтальной линии на уровне высоты 0, соединяющей две вертикальные линии
            profile_ax.plot([0, distance_kilometers], [0, 0], color='gray', linestyle='-',
                            label='Горизонтальная линия на уровне 0')

            # Добавление аннотации для максимального значения зоны Френеля
            max_fresnel_x = distance_kilometers / 2  # Середина профиля
            max_fresnel_y = ellipse_y_upper[num_points // 2]  # Максимальная высота эллипса
            profile_ax.annotate(f'Макс. зона Френеля: {radius_fresnel_1st_zone_meters:.2f} м',
                                xy=(max_fresnel_x, max_fresnel_y),
                                xytext=(max_fresnel_x, max_fresnel_y + 10),
                                arrowprops=dict(facecolor='black', shrink=0.05),
                                fontsize=10, color='black')

            profile_ax.legend()
            profile_ax.grid(True)

            plt.tight_layout()
            plt.show()

    # Метод отрисовки выбранной карты
    def plot_elevation_map(self):
        # Укажите путь к вашему файлу .hgt
        with rasterio.open(self.file_path) as src:
            self.width = src.width
            self.height = src.height
            self.bounds = src.bounds
            self.elevation_data = src.read(1)  # Чтение первого канала (высоты)

            # Получаем параметры трансформации
            transform = src.transform

            # Получаем размеры растрового изображения
            width = src.width
            height = src.height

            # Вычисляем координаты углов
            top_left = transform * (0, 0)  # Верхний левый угол
            top_right = transform * (width, 0)  # Верхний правый угол
            bottom_left = transform * (0, height)  # Нижний левый угол
            bottom_right = transform * (width, height)  # Нижний правый угол

            # Преобразуем координаты в формат DMS
            corners_dms = {
                "Верхний левый": top_left,
                "Верхний правый": top_right,
                "Нижний левый": bottom_left,
                "Нижний правый": bottom_right,
            }

            print("\nКоординаты углов карты (в градусах, минутах и секундах):")

            for corner, coords in corners_dms.items():
                lat_d, lat_m, lat_s = decimal_to_dms(abs(coords[1]))  # Широта
                lon_d, lon_m, lon_s = decimal_to_dms(abs(coords[0]))  # Долгота

                lat_direction = 'N' if coords[1] >= 0 else 'S'
                lon_direction = 'E' if coords[0] >= 0 else 'W'

                print(f"{corner}: Широта: {lat_d}° {lat_m}' {lat_s}\" {lat_direction}, "
                      f"Долгота: {lon_d}° {lon_m}' {lon_s}\" {lon_direction}")

            # Функция для расчета расстояния между двумя точками на поверхности Земли
            # Получение метаданных

        # Проверка на наличие ненулевых данных
        if self.elevation_data.size == 0:
            raise ValueError("Данные высоты пусты. Проверьте файл .hgt.")
        # Очистка текущей оси перед построением
        self.ax.clear()

        # Отображение карты высот
        cax = self.ax.imshow(self.elevation_data, cmap='terrain', origin='upper')

        # Добавление цветовой шкалы только если она еще не добавлена
        if self.colorbar is None:
            self.colorbar = self.canvas.figure.colorbar(cax, ax=self.ax, label='Elevation (meters)')
        self.colorbar.update_normal(cax)
        # Установка заголовка и подписей осей
        self.ax.set_title('Digital Elevation Model')
        self.ax.set_xlabel('Longitude Index')
        self.ax.set_ylabel('Latitude Index')

        # Обновление холста
        self.canvas.draw()

    # Метод сверяет, что выбраны ровно две точки, чтобы отобразить профиль местности, иначе ошибка
    def show_prof(self):
        if len(self.selected_points)==2:
            self.show_profile()
        else:
            QMessageBox.warning(self, "Ошибка ввода", "Должны быть введены ровно 2 точки.")
    # Метод очистки значений
    def clear_values(self):
        """Очистка выбранных точек и обновление карты."""
        self.selected_points.clear()  # Очищаем список выбранных точек

        self.plot_elevation_map()  # Повторно отображаем карту высот

        self.height_of_base_station_1 = 0
        self.height_of_base_station_2 = 0

        self.pushButton_set_point_on_map.setEnabled(True)

        self.pushButton_set_map_point1.setEnabled(True)
        self.pushButton_set_map_point2.setEnabled(False)

        self.pushButton_input_values_height_base_station.setEnabled(True)

    # Метод ручной установки точек
    def set_points(self):
        """
        Метод предназначен для установки на отображаемой карте двух точек в соответствии
        с введнными пользователем координатами. Метод считывает значения из объектов
        spinBox, преобразует их в пиксельные координаты, выполняя проверку выхода за границы
        карты, после чего отображает на карте. Если координаты выходят за границы, то в этом
        случае выдается предупреждение
        """

        #Блокируем кнопки установки точек на карте с помощью мыши(необходимо для того чтобы нельзя было
        #поставить координаты одной точки, а вторую установить нажатием мыши)
        self.pushButton_set_map_point1.setEnabled(False)
        self.pushButton_set_map_point2.setEnabled(False)
        # Получение значений для первой точки(географические координаты)(значения широты)
        lat_deg1 = int(self.spinBox_point1_latitude_gradus.value())
        lat_min1 = int(self.spinBox_point1_latitude_minutes.value())
        lat_sec1 = int(self.spinBox_point1_latitude_seconds.value())
        # Получение значений для первой точки(географические координаты)(значения долготы)
        lon_deg1 = int(self.spinBox_point1_longtitude_gradus.value())
        lon_min1 = int(self.spinBox_point1_longtitude_minutes.value())
        lon_sec1 = int(self.spinBox_point1_longtitude_seconds.value())

        # Преобразование в десятичный формат для первой точки(преобразуются в десятичные градусы)
        # Десятичные градусы упрощают вычисления и с ними работают многие библиотеки(также их удобно переводить в другие системы счисления)
        # Поэтому мы и выполняем перевод в десятичные градусы)
        latitude1 = lat_deg1 + (lat_min1 / 60) + (lat_sec1 / 3600)
        longitude1 = lon_deg1 + (lon_min1 / 60) + (lon_sec1 / 3600)

        # Сохраняем координаты первой точки с округлением(координаты первой точки сохраняются в массив)
        self.selected_points.append((round(latitude1, 4), round(longitude1, 4)))

        # Преобразование координат первой точки в индексы для отображения на графике
        # Благодаря пиксельным координатам можно отобразить точку на карте
        lon_index1 = int((longitude1 - self.bounds.left) / (self.bounds.right - self.bounds.left) * self.width)
        lat_index1 = int((self.bounds.top - latitude1) / (self.bounds.top - self.bounds.bottom) * self.height)

        # Получение значений для второй точки(географические координаты)(значения широты)
        lat_deg2 = int(self.spinBox_point2_latitude_gradus.value())
        lat_min2 = int(self.spinBox_point2_latitude_minutes.value())
        lat_sec2 = int(self.spinBox_point2_latitude_seconds.value())
        # Получение значений для второй точки(географические координаты)(значения долготы)
        lon_deg2 = int(self.spinBox_point2_longtitude_gradus.value())
        lon_min2 = int(self.spinBox_point2_longtitude_minutes.value())
        lon_sec2 = int(self.spinBox_point2_longtitude_seconds.value())

        # Преобразование в десятичный формат для второй точки(преобразуются в десятичные градусы)
        # Десятичные градусы упрощают вычисления и с ними работают многие библиотеки(также их удобно переводить в другие системы счисления)
        # Поэтому мы и выполняем перевод в десятичные градусы)
        latitude2 = lat_deg2 + (lat_min2 / 60) + (lat_sec2 / 3600)
        longitude2 = lon_deg2 + (lon_min2 / 60) + (lon_sec2 / 3600)

        # Сохраняем координаты второй точки с округлением(координаты второй точки сохраняются в массив)
        self.selected_points.append((round(latitude2, 4), round(longitude2, 4)))

        # Печать десятичных координат второй точки
        print(f"Установленная точка 2: Широта: {round(latitude2, 4)}, Долгота: {round(longitude2, 4)}")

        # Преобразование координат второй точки в индексы для отображения на графике
        # Благодаря пиксельным координатам можно отобразить точку на карте
        lon_index2 = int((longitude2 - self.bounds.left) / (self.bounds.right - self.bounds.left) * self.width)
        lat_index2 = int((self.bounds.top - latitude2) / (self.bounds.top - self.bounds.bottom) * self.height)

        # Проверка, находится ли точка внутри границ карты
        # В первом случае для первой точки
        if not (self.bounds.left <= longitude1 <= self.bounds.right and
                self.bounds.bottom <= latitude1 <= self.bounds.top):
            if not (self.bounds.left <= longitude2 <= self.bounds.right and
                self.bounds.bottom <= latitude2 <= self.bounds.top):
                    QMessageBox.warning(self, "ВНИМАНИЕ", "Введенные вами координаты выходят за пределы карты. Измените их!")
                    self.pushButton_set_map_point1.setEnabled(True)
                    self.pushButton_set_map_point2.setEnabled(False)
                    self.selected_points = []
            else:
                QMessageBox.warning(self, "ВНИМАНИЕ","Введенные вами координаты первой точки выходят за пределы карты. Измените их!")
                self.pushButton_set_map_point1.setEnabled(True)
                self.pushButton_set_map_point2.setEnabled(False)
                self.selected_points = []
        # Во втором случае для второй точки
        elif not (self.bounds.left <= longitude2 <= self.bounds.right and
                self.bounds.bottom <= latitude2 <= self.bounds.top):
            if not (self.bounds.left <= longitude1 <= self.bounds.right and
                    self.bounds.bottom <= latitude1 <= self.bounds.top):
                    QMessageBox.warning(self, "ВНИМАНИЕ", "Введенные вами координаты выходят за пределы карты. Измените их!")
                    self.pushButton_set_map_point1.setEnabled(True)
                    self.pushButton_set_map_point2.setEnabled(False)
                    self.selected_points = []
            else:
                QMessageBox.warning(self, "ВНИМАНИЕ", "Введенные вами координаты второй точки выходят за пределы карты. Измените их!")
                self.pushButton_set_map_point1.setEnabled(True)
                self.pushButton_set_map_point2.setEnabled(False)
                self.selected_points = []
        else:
            # Если все координаты в пределах карты, то производим их отображение в виде точек.
            # Отмечаем первую точку на графике
            self.ax.plot(lon_index1, lat_index1, 'ro')
            self.ax.text(lon_index1 + 10, lat_index1 + 10,
                         f'Точка 1: {self.selected_points[-2]}',
                         color='white', fontsize=10)

            # Отмечаем вторую точку на графике
            self.ax.plot(lon_index2, lat_index2, 'ro')
            self.ax.text(lon_index2 + 10, lat_index2 + 10,
                         f'Точка 2: {self.selected_points[-1]}',
                         color='white', fontsize=10)
            #Функция, которая производит обновление графика, чтобы отобразить точки
            self.canvas.draw()


if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS  # Путь к временной директории при запуске из EXE
    else:
        base_path = os.path.dirname(__file__)

    image_path = os.path.join(base_path, 'fon', 'picture.jpg')

    app = QtWidgets.QApplication(sys.argv)
    form = Form_main()
    palette = QPalette()
    palette.setBrush(QPalette.Background, QBrush(QPixmap(image_path)))
    form.setPalette(palette)
    form.show()
    sys.exit(app.exec_())