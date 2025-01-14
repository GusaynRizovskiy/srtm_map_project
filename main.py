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

# Вычисление расстояний в метрах
x_distance_m = (bounds.right - bounds.left)  # В метрах
y_distance_m = (bounds.top - bounds.bottom)   # В метрах

# Получение координат углов
top_left = (bounds.left, bounds.top)
top_right = (bounds.right, bounds.top)
bottom_left = (bounds.left, bounds.bottom)
bottom_right = (bounds.right, bounds.bottom)

# Вычисление разрешения
resolution_x = (bounds.right - bounds.left) / width  # Разрешение по X в метрах на пиксель
resolution_y = (bounds.top - bounds.bottom) / height  # Разрешение по Y в метрах на пиксель

# Преобразование системы координат в понятный вид
crs_str = str(crs).replace('EPSG:', 'EPSG: ') if crs else 'Неизвестная система координат'

# Получение статистики высот
min_elevation = np.min(elevation_data)
max_elevation = np.max(elevation_data)
mean_elevation = np.mean(elevation_data)

# Вывод информации о карте
print(f"Размерность: {width} x {height} пикселей")
print(f"Разрешение: {resolution_x:.2f} м/пиксель по X, {resolution_y:.2f} м/пиксель по Y")
print(f"Система координат: {crs_str}")
print(f"Расстояние между краями карты: {x_distance_m:.2f} м (по ширине), {y_distance_m:.2f} м (по высоте)")
print(f"Координаты углов:")
print(f"  Верхний левый: {top_left}")
print(f"  Верхний правый: {top_right}")
print(f"  Нижний левый: {bottom_left}")
print(f"  Нижний правый: {bottom_right}")
print(f"Минимальная высота: {min_elevation} метров")
print(f"Максимальная высота: {max_elevation} метров")
print(f"Средняя высота: {mean_elevation:.2f} метров")

# Отображение карты высот
plt.figure(figsize=(10, 6))
plt.imshow(elevation_data, cmap='terrain', origin='upper')
plt.colorbar(label='Elevation (meters)')
plt.title('Digital Elevation Model')
plt.xlabel('Longitude Index')
plt.ylabel('Latitude Index')
plt.axis('off')  # Убираем оси для лучшего отображения
plt.show()
