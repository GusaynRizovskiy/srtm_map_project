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


# Функция для построения профиля местности между двумя точками с учетом кривизны Земли и отображения первой зоны Френеля как эллипса по зеленой линии.
def show_profile(event):
    if len(selected_points) == 2:
        lon1, lat1 = selected_points[0]
        lon2, lat2 = selected_points[1]

        # Получаем индексы пикселей для выбранных точек
        x1 = int((lon1 - bounds.left) / (bounds.right - bounds.left) * width)
        y1 = int((bounds.top - lat1) / (bounds.top - bounds.bottom) * height)

        x2 = int((lon2 - bounds.left) / (bounds.right - bounds.left) * width)
        y2 = int((bounds.top - lat2) / (bounds.top - bounds.bottom) * height)

        # Генерируем количество интерполированных точек на основе разницы индексов пикселей
        num_points = max(abs(x2 - x1), abs(y2 - y1)) + 1

        # Генерация линейных интерполированных значений долготы и широты
        lons_interp = np.linspace(lon1, lon2, num_points)
        lats_interp = np.linspace(lat1, lat2, num_points)

        elevations = []

        for lon, lat in zip(lons_interp, lats_interp):
            x_index = int((lon - bounds.left) / (bounds.right - bounds.left) * width)
            y_index = int((bounds.top - lat) / (bounds.top - bounds.bottom) * height)
            elevations.append(elevation_data[y_index, x_index])

        # Вычисление расстояния между двумя точками
        distance_meters = haversine(selected_points[0], selected_points[1])
        radius_fresnel_1st_zone_meters = np.sqrt(distance_meters / (4 * np.pi))

        print(f"Радиус первой зоны Френеля: {radius_fresnel_1st_zone_meters:.2f} метров")

        if hasattr(show_profile, 'profile_fig') and show_profile.profile_fig is not None:
            plt.close(show_profile.profile_fig)

        # Построение графика профиля местности
        show_profile.profile_fig, profile_ax = plt.subplots(figsize=(10, 5))
        profile_ax.plot(np.linspace(0, distance_kilometers := distance_meters / 1000.0, num_points), elevations)

        profile_ax.set_title('Профиль местности')
        profile_ax.set_xlabel('Расстояние (км)')
        profile_ax.set_ylabel('Высота (метры)')

        # Генерация синусоидальной верхней границы эллипса
        t = np.linspace(0, np.pi, num_points)

        # Синусоида с учетом радиуса зоны Френеля
        sinusoidal_variation = radius_fresnel_1st_zone_meters * np.sin(t)

        elevation_start = elevations[0]
        elevation_end = elevations[-1]

        # Линейная интерполяция высот между начальной и конечной точками
        linear_elevation_line = np.linspace(elevation_start, elevation_end, num_points)

        # Верхняя граница эллипса с учетом синусоиды
        ellipse_y_upper = linear_elevation_line + sinusoidal_variation

        # Построение верхней границы эллипса
        profile_ax.plot(np.linspace(0, distance_kilometers, num_points), ellipse_y_upper,
                        color='yellow', linestyle='-', label='Верхняя граница зоны Френеля')

        # Добавление зеленой линии между двумя точками на профиле местности
        profile_ax.plot([0, distance_kilometers], [elevations[0], elevations[-1]], color='green', linestyle='--',
                        label='Прямая линия')

        # Определение середины зеленой линии
        mid_distance_km = distance_kilometers / 2
        mid_elevation = np.interp(mid_distance_km, [0, distance_kilometers], [elevations[0], elevations[-1]])

        # Отметка точки середины на графике
        profile_ax.plot(mid_distance_km, mid_elevation, 'bo', label='Середина зеленой линии')

        # Построение радиуса зоны Френеля от середины зеленой линии перпендикулярно к синусоиде
        fresnel_top_y = mid_elevation + radius_fresnel_1st_zone_meters

        profile_ax.plot([mid_distance_km], [fresnel_top_y],
                        color='purple', marker='o', label='Пересечение синусоиды')

        # Отметка точки максимума синусоиды на графике
        profile_ax.legend()
        plt.show()


# Функция для очистки выбранных точек и обновления графика
def clear_values(event):
    global selected_points

    selected_points.clear()  # Очищаем список выбранных точек

    ax.cla()  # Очищаем ось

    # Повторно отображаем карту высот без точек и меток
    cax = ax.imshow(elevation_data, cmap='terrain', origin='upper')

    # Установка заголовка и подписей осей
    ax.set_title('Digital Elevation Model')
    ax.set_xlabel('Longitude Index')
    ax.set_ylabel('Latitude Index')

    plt.axis('on')  # Включаем отображение осей

    plt.draw()  # Обновляем график


# Подключаем обработчик событий клика мыши и кнопку "Отобразить Профиль"
cid_click = fig.canvas.mpl_connect('button_press_event', onclick)

button_ax_show_profile = fig.add_axes([0.05, 0.01, 0.15, 0.05])
button_show_profile = plt.Button(button_ax_show_profile, 'Отобразить Профиль')
button_show_profile.on_clicked(show_profile)

button_ax_clear_values = fig.add_axes([0.05, 0.07, 0.15, 0.05])
button_clear_values = plt.Button(button_ax_clear_values, 'Очистить значения')
button_clear_values.on_clicked(clear_values)

plt.show()
