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
top_left = (bounds.left, bounds.top)  # (долгота, широта)
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

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
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
print(
    f"Размерность в километрах: {width_distance_m / 1000:.2f} км (по ширине), {height_distance_m / 1000:.2f} км (по высоте)")
print(
    f"Разрешение: {resolution_width_m_per_pixel:.2f} м/пиксель (по ширине), {resolution_height_m_per_pixel:.2f} м/пиксель (по высоте)")
print(f"Система координат: {str(crs).replace('EPSG:', 'EPSG: ') if crs else 'Неизвестная система координат'}")
print(f"Координаты углов:")
print(f"  Верхний левый: {top_left}")
print(f"  Верхний правый: {top_right}")
print(f"  Нижний левый: {bottom_left}")
print(f"  Нижний правый: {bottom_right}")

# Отображение карты высот
fig, ax = plt.subplots(figsize=(10, 6))
cax = ax.imshow(elevation_data, cmap='terrain', origin='upper')
plt.colorbar(cax, label='Elevation (meters)')
plt.title('Digital Elevation Model')
plt.xlabel('Longitude Index')
plt.ylabel('Latitude Index')
plt.axis('off')  # Убираем оси для лучшего отображения

# Список для хранения выбранных точек с географическими координатами
selected_points = []


# Функция для обработки кликов мыши
def onclick(event):
    if len(selected_points) < 2:
        # Конвертируем пиксели в географические координаты
        lon = bounds.left + (event.xdata / width) * (bounds.right - bounds.left)
        lat = bounds.top - (event.ydata / height) * (bounds.top - bounds.bottom)

        # Сохраняем географические координаты точки с округлением до 4 знаков после запятой
        selected_points.append((round(lon, 4), round(lat, 4)))

        # Отмечаем точку на изображении
        ax.plot(event.xdata, event.ydata, 'ro')  # Красная точка

        # Определяем номер точки для отображения метки
        point_number = len(selected_points)

        # Выводим координаты точки на графике с явным преобразованием в строку и округлением
        ax.text(event.xdata + 10, event.ydata + 10,
                f'Точка {point_number}: ({selected_points[-1][0]}, {selected_points[-1][1]})',
                color='white', fontsize=10)

        plt.draw()  # Обновляем график

    if len(selected_points) == 2:
        print("Выбраны точки:")
        for i, point in enumerate(selected_points):
            print(f"Точка {i + 1}: {point}")


# Функция для построения профиля местности между двумя точками и вычисления расстояния в километрах
def show_profile(event):
    if len(selected_points) == 2:
        lon1, lat1 = selected_points[0]
        lon2, lat2 = selected_points[1]

        # Получаем индексы пикселей для выбранных точек
        x1 = int((lon1 - bounds.left) / (bounds.right - bounds.left) * width)
        y1 = int((bounds.top - lat1) / (bounds.top - bounds.bottom) * height)

        x2 = int((lon2 - bounds.left) / (bounds.right - bounds.left) * width)
        y2 = int((bounds.top - lat2) / (bounds.top - bounds.bottom) * height)

        # Генерируем линейные интерполированные точки между двумя выбранными точками
        num_points = max(abs(x2-x1),abs(y2-y1))+1  # Устанавливаем количество интерполированных точек

        x_values = np.linspace(x1, x2, num_points).astype(int)
        y_values = np.linspace(y1, y2, num_points).astype(int)

        # Получаем высоты для интерполированных точек
        elevations = elevation_data[y_values, x_values]

        # Вычисляем расстояние между двумя точками в метрах и переводим в километры
        distance_meters = haversine(selected_points[0], selected_points[1])
        distance_kilometers = distance_meters / 1000.0

        # Проверяем существование графика профиля и закрываем его при необходимости
        if hasattr(show_profile, 'profile_fig') and show_profile.profile_fig is not None:
            plt.close(show_profile.profile_fig)

        # Построение нового графика профиля местности
        show_profile.profile_fig, profile_ax = plt.subplots(figsize=(10, 5))

        profile_ax.plot(np.arange(num_points), elevations)

        profile_ax.set_title('Профиль местности')

        profile_ax.set_xlabel('Расстояние (км)')  # Изменяем название оси X на "Расстояние (км)"

        # Устанавливаем метки по оси X с учетом расстояния между точками и переводим в километры
        tick_locations = np.linspace(0, num_points - 1, num=15).astype(int)  # Местоположения меток на оси X

        tick_labels = [f"{distance_kilometers * i / (num_points - 1):.2f}" for i in tick_locations]

        profile_ax.set_xticks(tick_locations)
        profile_ax.set_xticklabels(tick_labels)

        profile_ax.set_ylabel('Высота (метры)')

        plt.show()


# Подключаем обработчик событий клика мыши и кнопку "Отобразить Профиль"
cid_click = fig.canvas.mpl_connect('button_press_event', onclick)

button_ax = fig.add_axes([0.8, 0.01, 0.15, 0.05])
button_show_profile = plt.Button(button_ax, 'Отобразить Профиль')

button_show_profile.on_clicked(show_profile)

plt.show()
