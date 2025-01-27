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

        # Отрисовка карты
        self.pushButton_load_map.clicked.connect(self.open_file_dialog)

        self.pushButton_show_graphic.clicked.connect(self.show_prof)

        self.pushButton_clean_values.clicked.connect(self.clear_values)

        self.pushButton_set_map_point1.clicked.connect(self.prepare_point1_selection)
        self.pushButton_set_map_point2.clicked.connect(self.prepare_point2_selection)

        self.pushButton_set_point_on_map.clicked.connect(self.set_points)

        #Устанавливаем блокировку на кнопки до момента загрузки карты в программе
        self.pushButton_set_point_on_map.setEnabled(False)
        self.pushButton_set_map_point1.setEnabled(False)
        self.pushButton_set_map_point2.setEnabled(False)
        self.pushButton_input_values_height_base_station.setEnabled(False)
        self.pushButton_show_graphic.setEnabled(False)
        self.pushButton_clean_values.setEnabled(False)



    def open_file_dialog(self):
        if len(self.selected_points)>0:
            QMessageBox.warning(self, "ВНИМАНИЕ", "Перед загрузкой другой карты необходимо провести очистку значений.")
        else:
            # Open the file dialog
            options = QFileDialog.Options()
            self.file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "",
                                                       "Все файлы (*.*);;Текстовые файлы (*.txt);;Изображения (*.png *.jpg);;HGT файлы (*.hgt)",
                                                       options=options)
            # Check if a file was selected
            if self.file_path:
                # Check if the file exists
                if os.path.isfile(self.file_path):
                    # Check if the file extension is .hgt
                    if self.file_path.endswith('.hgt'):
                        self.plot_elevation_map()  # Call your method to plot the elevation map
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

    def prepare_point1_selection(self):
        """Подготовка к выбору первой точки"""
        if len(self.selected_points) == 0:
            self.pushButton_set_map_point1.setEnabled(False)
            self.canvas.mpl_connect('button_press_event', self.onclick_point1)

    def prepare_point2_selection(self):
        """Подготовка к выбору второй точки"""
        if len(self.selected_points) == 1:
            self.pushButton_set_map_point2.setEnabled(False)
            self.canvas.mpl_connect('button_press_event', self.onclick_point2)

    def onclick_point1(self, event):
        self.pushButton_set_point_on_map.setEnabled(False)
        self.pushButton_clean_values.setEnabled(True)
        self.pushButton_load_map.setEnabled(False)
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

            profile_fig, profile_ax = plt.subplots(figsize=(10, 5))
            distance_kilometers = distance_meters / 1000.0

            profile_ax.plot(np.linspace(0, distance_kilometers, num_points), elevations,
                            color='blue', label='Профиль рельефа')

            profile_ax.set_title('Профиль местности')
            profile_ax.set_xlabel('Расстояние (км)')
            profile_ax.set_ylabel('Высота (метры)')

            # Генерация синусоидальной верхней границы эллипса
            sinusoidal_variation = radius_fresnel_1st_zone_meters * np.sin(np.linspace(0, np.pi, num_points))

            elevation_start = elevations[0]
            elevation_end = elevations[-1]

            linear_elevation_line = np.linspace(elevation_start, elevation_end, num_points)
            ellipse_y_upper = linear_elevation_line + sinusoidal_variation

            # Построение верхней границы эллипса
            profile_ax.plot(np.linspace(0, distance_kilometers, num_points), ellipse_y_upper,
                            color='yellow', linestyle='-', label='Верхняя граница зоны Френеля')

            # Добавление прямой линии между точками
            profile_ax.plot([0, distance_kilometers], [elevations[0], elevations[-1]],
                            color='green', linestyle='--', label='Прямая линия')

            profile_ax.legend()
            profile_ax.grid(True)

            plt.tight_layout()
            plt.show()

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

        # Установка заголовка и подписей осей
        self.ax.set_title('Digital Elevation Model')
        self.ax.set_xlabel('Longitude Index')
        self.ax.set_ylabel('Latitude Index')

        # Обновление холста
        self.canvas.draw()

    def show_prof(self):
        if len(self.selected_points)==2:
            self.show_profile()
        else:
            QMessageBox.warning(self, "Ошибка ввода", "Должны быть введены ровно 2 точки.")
    def clear_values(self):
        """Очистка выбранных точек и обновление карты."""
        self.selected_points.clear()  # Очищаем список выбранных точек

        self.plot_elevation_map()  # Повторно отображаем карту высот

        self.pushButton_set_point_on_map.setEnabled(True)

        self.pushButton_set_map_point1.setEnabled(True)
        self.pushButton_set_map_point2.setEnabled(True)

    def set_points(self):
        self.pushButton_set_map_point1.setEnabled(False)
        self.pushButton_set_map_point2.setEnabled(False)
        # Получение значений для первой точки
        lat_deg1 = int(self.spinBox_point1_latitude_gradus.value())
        lat_min1 = int(self.spinBox_point1_latitude_minutes.value())
        lat_sec1 = int(self.spinBox_point1_latitude_seconds.value())

        lon_deg1 = int(self.spinBox_point1_longtitude_gradus.value())
        lon_min1 = int(self.spinBox_point1_longtitude_minutes.value())
        lon_sec1 = int(self.spinBox_point1_longtitude_seconds.value())

        # Преобразование в десятичный формат для первой точки
        latitude1 = lat_deg1 + (lat_min1 / 60) + (lat_sec1 / 3600)
        longitude1 = lon_deg1 + (lon_min1 / 60) + (lon_sec1 / 3600)

        # Сохраняем координаты первой точки с округлением
        self.selected_points.append((round(latitude1, 4), round(longitude1, 4)))

        # Печать десятичных координат первой точки
        print(f"Установленная точка 1: Широта: {round(latitude1, 4)}, Долгота: {round(longitude1, 4)}")

        # Преобразование координат первой точки в индексы для отображения на графике
        lon_index1 = int((longitude1 - self.bounds.left) / (self.bounds.right - self.bounds.left) * self.width)
        lat_index1 = int((self.bounds.top - latitude1) / (self.bounds.top - self.bounds.bottom) * self.height)

        # Получение значений для второй точки
        lat_deg2 = int(self.spinBox_point2_latitude_gradus.value())
        lat_min2 = int(self.spinBox_point2_latitude_minutes.value())
        lat_sec2 = int(self.spinBox_point2_latitude_seconds.value())

        lon_deg2 = int(self.spinBox_point2_longtitude_gradus.value())
        lon_min2 = int(self.spinBox_point2_longtitude_minutes.value())
        lon_sec2 = int(self.spinBox_point2_longtitude_seconds.value())

        # Преобразование в десятичный формат для второй точки
        latitude2 = lat_deg2 + (lat_min2 / 60) + (lat_sec2 / 3600)
        longitude2 = lon_deg2 + (lon_min2 / 60) + (lon_sec2 / 3600)

        # Сохраняем координаты второй точки с округлением
        self.selected_points.append((round(latitude2, 4), round(longitude2, 4)))

        # Печать десятичных координат второй точки
        print(f"Установленная точка 2: Широта: {round(latitude2, 4)}, Долгота: {round(longitude2, 4)}")

        # Преобразование координат второй точки в индексы для отображения на графике
        lon_index2 = int((longitude2 - self.bounds.left) / (self.bounds.right - self.bounds.left) * self.width)
        lat_index2 = int((self.bounds.top - latitude2) / (self.bounds.top - self.bounds.bottom) * self.height)

        # Проверка, находится ли точка внутри границ карты
        if not (self.bounds.left <= longitude1 <= self.bounds.right and
                self.bounds.bottom <= latitude1 <= self.bounds.top):
            if not (self.bounds.left <= longitude2 <= self.bounds.right and
                self.bounds.bottom <= latitude2 <= self.bounds.top):
                    QMessageBox.warning(self, "ВНИМАНИЕ", "Введенные вами координаты выходят за пределы карты. Измените их!")
        else:
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


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = Form_main()
    palette = QPalette()
    palette.setBrush(QPalette.Background, QBrush(QPixmap("picture.jpg")))
    form.setPalette(palette)
    form.show()
    sys.exit(app.exec_())