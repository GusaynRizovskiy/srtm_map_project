import numpy as np
import rasterio


def load_hgt_matrix(path):
    """Читает файл и возвращает матрицу высот и границы (extent) для отрисовки."""
    with rasterio.open(path) as src:
        # Читаем первый канал (высоты)
        matrix = src.read(1)
        # Определяем границы (Left, Right, Bottom, Top) для matplotlib
        bounds = src.bounds
        extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
        return matrix, extent


def haversine(coord1, coord2):
    R = 6371e3
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


def get_elevation_profile(raster_path, p1, p2, num_points=250):
    """p1, p2 это кортежи (lat, lon)"""
    with rasterio.open(raster_path) as src:
        # Создаем массив точек между началом и концом
        lats = np.linspace(p1[0], p2[0], num_points)
        lons = np.linspace(p1[1], p2[1], num_points)

        # В rasterio.sample передаются пары (lon, lat)
        coords = list(zip(lons, lats))
        elevations = [val[0] for val in src.sample(coords)]

        # Расстояния в метрах от первой точки
        distances = [haversine(p1, (lats[i], lons[i])) for i in range(num_points)]
        return np.array(distances), np.array(elevations)