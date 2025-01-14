import numpy as np
import matplotlib.pyplot as plt
import rasterio

# Укажите путь к вашему файлу .hgt
hgt_file_path = 'N40E018.hgt/N40E018.hgt'

# Чтение данных из файла .hgt
with rasterio.open(hgt_file_path) as src:
    elevation_data = src.read(1)  # Чтение первого канала (высоты)

    # Получение метаданных
    width = src.width
    height = src.height
    bounds = src.bounds
    crs = src.crs

# Проверка на наличие ненулевых данных
if elevation_data.size == 0:
    raise ValueError("Данные высоты пусты. Проверьте файл .hgt.")

# Получение координат углов
top_left = (bounds.left, bounds.top)      # (долгота, широта)
top_right = (bounds.right, bounds.top)
bottom_left = (bounds.left, bounds.bottom)
bottom_right = (bounds.right, bounds.bottom)

# Функция для расчета расстояния между двумя точками на поверхности Земли
def haversine(coord1, coord2):
    R = 6371e3  # Радиус Земли в метрах
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    distance = R * c  # Расстояние в метрах
    return distance

# Расчет расстояний между углами карты
width_distance_m = haversine(top_left, top_right)
height_distance_m = haversine(top_left, bottom_left)

# Вычисление разрешения в метрах на пиксель
resolution_width_m_per_pixel = width_distance_m / width  # Разрешение по ширине
resolution_height_m_per_pixel = height_distance_m / height  # Разрешение по высоте

# Вывод информации о карте
print(f"Размерность: {width} x {height} пикселей")
print(f"Размерность в километрах: {width_distance_m / 1000:.2f} км (по ширине), {height_distance_m / 1000:.2f} км (по высоте)")
print(f"Разрешение: {resolution_width_m_per_pixel:.2f} м/пиксель (по ширине), {resolution_height_m_per_pixel:.2f} м/пиксель (по высоте)")
print(f"Система координат: {str(crs).replace('EPSG:', 'EPSG: ') if crs else 'Неизвестная система координат'}")
print(f"Координаты углов:")
print(f"  Верхний левый: {top_left}")
print(f"  Верхний правый: {top_right}")
print(f"  Нижний левый: {bottom_left}")
print(f"  Нижний правый: {bottom_right}")

# Отображение карты высот
plt.figure(figsize=(10, 6))
plt.imshow(elevation_data, cmap='terrain', origin='upper')
plt.colorbar(label='Elevation (meters)')
plt.title('Digital Elevation Model')
plt.xlabel('Longitude Index')
plt.ylabel('Latitude Index')
plt.axis('off')  # Убираем оси для лучшего отображения
plt.show()
