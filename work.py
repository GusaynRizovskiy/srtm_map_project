import sys
import numpy as np
import rasterio
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPalette, QBrush, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from form_of_window import Form1

# Укажите путь к вашему файлу .hgt
hgt_file_path = 'N40E018.hgt/N40E018.hgt'
def decimal_to_dms(degrees):
    """Преобразует десятичные градусы в градусы, минуты и секунды."""
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = (degrees - d - m / 60) * 3600
    return d, m, round(s, 2)  # Округляем секунды до двух знаков после запятой


# Укажите путь к вашему файлу .hgt
hgt_file_path = 'N40E018.hgt/N40E018.hgt'

# Чтение данных из файла .hgt
with rasterio.open(hgt_file_path) as src:
    elevation_data = src.read(1)  # Чтение первого канала (высоты)

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
    width = src.width
    height = src.height
    bounds = src.bounds

# Проверка на наличие ненулевых данных
if elevation_data.size == 0:
    raise ValueError("Данные высоты пусты. Проверьте файл .hgt.")

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
        self.plot_elevation_map()

        self.pushButton_clean_values.clicked.connect(self.clear_values)

        self.pushButton_set_map_point1.clicked.connect(self.prepare_point1_selection)
        self.pushButton_set_map_point2.clicked.connect(self.prepare_point2_selection)

        self.pushButton_set_point_on_map.clicked.connect(self.set_points)

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
        """Обработчик клика для первой точки"""
        if event.xdata is not None and event.ydata is not None:
            lon_index = int(event.xdata)
            lat_index = int(event.ydata)
            lon = bounds.left + (lon_index / width) * (bounds.right - bounds.left)
            lat = bounds.top - (lat_index / height) * (bounds.top - bounds.bottom)

            self.selected_points.append((round(lat, 4), round(lon, 4)))

            # Отмечаем первую точку
            self.ax.plot(event.xdata, event.ydata, 'ro')
            self.ax.text(event.xdata + 10, event.ydata + 10,
                         f'Точка 1: {self.selected_points[-1]}',
                         color='white', fontsize=10)

            self.canvas.draw()
            self.canvas.mpl_disconnect(self.canvas.mpl_connect('button_press_event', self.onclick_point1))

    def onclick_point2(self, event):
        """Обработчик клика для второй точки"""
        if event.xdata is not None and event.ydata is not None:
            lon_index = int(event.xdata)
            lat_index = int(event.ydata)
            lon = bounds.left + (lon_index / width) * (bounds.right - bounds.left)
            lat = bounds.top - (lat_index / height) * (bounds.top - bounds.bottom)

            self.selected_points.append((round(lat, 4), round(lon, 4)))

            # Отмечаем вторую точку
            self.ax.plot(event.xdata, event.ydata, 'ro')
            self.ax.text(event.xdata + 10, event.ydata + 10,
                         f'Точка 2: {self.selected_points[-1]}',
                         color='white', fontsize=10)

            self.canvas.draw()
            self.canvas.mpl_disconnect(self.canvas.mpl_connect('button_press_event', self.onclick_point2))

    def show_profile(self):
        """Отображение профиля местности между двумя выбранными точками."""
        plt.close('all')

        if len(self.selected_points) == 2:
            lat1, lon1 = self.selected_points[0]
            lat2, lon2 = self.selected_points[1]

            x1 = int((lon1 - bounds.left) / (bounds.right - bounds.left) * width)
            y1 = int((bounds.top - lat1) / (bounds.top - bounds.bottom) * height)

            x2 = int((lon2 - bounds.left) / (bounds.right - bounds.left) * width)
            y2 = int((bounds.top - lat2) / (bounds.top - bounds.bottom) * height)

            num_points = max(abs(x2 - x1), abs(y2 - y1)) + 1

            lons_interp = np.linspace(lon1, lon2, num_points)
            lats_interp = np.linspace(lat1, lat2, num_points)

            elevations = []

            for lon, lat in zip(lons_interp, lats_interp):
                x_index = int((lon - bounds.left) / (bounds.right - bounds.left) * width)
                y_index = int((bounds.top - lat) / (bounds.top - bounds.bottom) * height)
                elevations.append(elevation_data[y_index, x_index])

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
        # Очистка текущей оси перед построением
        self.ax.clear()

        # Отображение карты высот
        cax = self.ax.imshow(elevation_data, cmap='terrain', origin='upper')

        # Добавление цветовой шкалы только если она еще не добавлена
        if self.colorbar is None:
            self.colorbar = self.canvas.figure.colorbar(cax, ax=self.ax, label='Elevation (meters)')

        # Установка заголовка и подписей осей
        self.ax.set_title('Digital Elevation Model')
        self.ax.set_xlabel('Longitude Index')
        self.ax.set_ylabel('Latitude Index')

        # Обновление холста
        self.canvas.draw()
        self.pushButton_show_graphic.clicked.connect(self.show_prof)


    def show_prof(self):
        if len(self.selected_points)==2:
            self.show_profile()
    def clear_values(self):
        """Очистка выбранных точек и обновление карты."""
        self.selected_points.clear()  # Очищаем список выбранных точек

        self.plot_elevation_map()  # Повторно отображаем карту высот

        self.pushButton_set_map_point1.setEnabled(True)
        self.pushButton_set_map_point2.setEnabled(True)

    def set_points(self):
        """Устанавливает точки на карте на основе значений из спин боксов"""
        lat_deg = int(self.spinBox_point1_latitude_gradus.value())
        lat_min = int(self.spinBox_point1_latitude_minutes.value())
        lat_sec = int(self.spinBox_point1_latitude_seconds.value())

        lon_deg = int(self.spinBox_point1_longtitude_gradus.value())
        lon_min = int(self.spinBox_point1_longtitude_minutes.value())
        lon_sec = int(self.spinBox_point1_longtitude_seconds.value())

        # Преобразование в десятичный формат
        latitude = lat_deg + (lat_min / 60) + (lat_sec / 3600)
        longitude = lon_deg + (lon_min / 60) + (lon_sec / 3600)

        # Сохраняем координаты с округлением
        self.selected_points.append((round(latitude, 4), round(longitude, 4)))

        # Отмечаем точку на графике
        x_data = (longitude - self.bounds[0]) / (self.bounds[1] - self.bounds[0]) * self.fig.get_size_inches()[0]
        y_data = (self.bounds[3] - latitude) / (self.bounds[3] - self.bounds[2]) * self.fig.get_size_inches()[1]

        self.ax.plot(x_data, y_data, 'ro')
        self.ax.text(x_data + 10, y_data + 10,
                     f'Точка {len(self.selected_points)}: {self.selected_points[-1]}',
                     color='white', fontsize=10)

        self.canvas.draw()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = Form_main()
    palette = QPalette()
    palette.setBrush(QPalette.Background, QBrush(QPixmap("picture.webp")))
    form.setPalette(palette)
    form.show()
    sys.exit(app.exec_())