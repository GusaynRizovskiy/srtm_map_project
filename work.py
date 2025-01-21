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

# Чтение данных из файла .hgt
with rasterio.open(hgt_file_path) as src:
    elevation_data = src.read(1)  # Чтение первого канала (высоты)

    # Получение метаданных
    width = src.width
    height = src.height
    bounds = src.bounds

# Проверка на наличие ненулевых данных
if elevation_data.size == 0:
    raise ValueError("Данные высоты пусты. Проверьте файл .hgt.")


# Функция для расчета расстояния между двумя точками на поверхности Земли
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

            distance_meters = haversine(self.selected_points[0], self.selected_points[1])
            radius_fresnel_1st_zone_meters = np.sqrt(distance_meters / (4 * np.pi))

            print(f"Радиус первой зоны Френеля: {radius_fresnel_1st_zone_meters:.2f} метров")

            profile_fig, profile_ax = plt.subplots(figsize=(10, 5))
            distance_kilometers = distance_meters / 1000.0

            profile_ax.plot(np.linspace(0, distance_kilometers, num_points), elevations)

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

            # Указание точки максимума синусоиды
            max_sinusoid_x_km = distance_kilometers / 2  # Максимум находится в середине
            max_sinusoid_y = elevation_start + radius_fresnel_1st_zone_meters  # Высота максимума

            # Добавление зеленой линии между двумя точками на профиле местности
            profile_ax.plot([0, distance_kilometers], [elevations[0], elevations[-1]], color='green', linestyle='--',
                            label='Прямая линия')

            mid_distance_km = distance_kilometers / 2
            mid_elevation = np.interp(mid_distance_km, [0, distance_kilometers], [elevations[0], elevations[-1]])

            fresnel_top_y = mid_elevation + radius_fresnel_1st_zone_meters

            profile_ax.legend()

            plt.show()  # Отображаем профиль
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
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = Form_main()
    palette = QPalette()
    palette.setBrush(QPalette.Background, QBrush(QPixmap("picture.webp")))
    form.setPalette(palette)
    form.show()
    sys.exit(app.exec_())