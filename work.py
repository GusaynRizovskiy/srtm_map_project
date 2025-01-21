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
        self.pushButton_set_map_point1.clicked.connect(self.canvas_connect_point_1)
        self.pushButton_set_map_point2.clicked.connect(self.canvas_connect_point_2)
    def canvas_connect_point_1(self):
        self.canvas.mpl_connect('button_press_event', self.onclick_point1)
    def canvas_connect_point_2(self):
        self.canvas.mpl_connect('button_press_event', self.onclick_point2)
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
    def onclick_point1(self, event):
        """Обработка кликов мыши на графике."""
        if len(self.selected_points) < 1 and event.xdata is not None and event.ydata is not None:
            lon_index = int(event.xdata)
            lat_index = int(event.ydata)
            lon = bounds.left + (lon_index / width) * (bounds.right - bounds.left)
            lat = bounds.top - (lat_index / height) * (bounds.top - bounds.bottom)
            self.selected_points.append((round(lat, 4), round(lon, 4)))  # Сохраняем как (широта, долгота)

            # Отмечаем точку на изображении
            self.ax.plot(event.xdata, event.ydata, 'ro')  # Красная точка
            point_number = len(self.selected_points)
            self.ax.text(event.xdata + 10, event.ydata + 10,
                         f'Точка {point_number}: ({self.selected_points[-1][0]}, {self.selected_points[-1][1]})',
                         color='white', fontsize=10)

            self.canvas.draw()  # Обновляем график
    def onclick_point2(self, event):
        """Обработка кликов мыши на графике."""
        if len(self.selected_points) < 2 and event.xdata is not None and event.ydata is not None:
            lon_index = int(event.xdata)
            lat_index = int(event.ydata)
            lon = bounds.left + (lon_index / width) * (bounds.right - bounds.left)
            lat = bounds.top - (lat_index / height) * (bounds.top - bounds.bottom)
            self.selected_points.append((round(lat, 4), round(lon, 4)))  # Сохраняем как (широта, долгота)

            # Отмечаем точку на изображении
            self.ax.plot(event.xdata, event.ydata, 'ro')  # Красная точка
            point_number = len(self.selected_points)
            self.ax.text(event.xdata + 10, event.ydata + 10,
                         f'Точка {point_number}: ({self.selected_points[-1][0]}, {self.selected_points[-1][1]})',
                         color='white', fontsize=10)

            self.canvas.draw()  # Обновляем график

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = Form_main()
    palette = QPalette()
    palette.setBrush(QPalette.Background, QBrush(QPixmap("picture.webp")))
    form.setPalette(palette)
    form.show()
    sys.exit(app.exec_())