import numpy as np
import matplotlib.pyplot as plt
import rasterio

# Укажите путь к вашему файлу .hgt
hgt_file_path = 'N40E018.hgt/N40E018.hgt'

# Чтение данных из файла .hgt
with rasterio.open(hgt_file_path) as src:
    elevation_data = src.read(1)  # Чтение первого канала (высоты)

# Проверка на наличие ненулевых данных
if elevation_data.size == 0:
    raise ValueError("Данные высоты пусты. Проверьте файл .hgt.")

# Отображение карты высот
plt.figure(figsize=(10, 6))
plt.imshow(elevation_data, cmap='terrain', origin='upper')
plt.colorbar(label='Elevation (meters)')
plt.title('Digital Elevation Model')
plt.xlabel('Longitude Index')
plt.ylabel('Latitude Index')
plt.axis('off')  # Убираем оси для лучшего отображения
plt.show()
