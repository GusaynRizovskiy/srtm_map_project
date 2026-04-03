import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter.filedialog as fd
import numpy as np
import app_logic

# Устанавливаем глобальную светлую тему
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class RadioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Радиосвязь: Инженерный расчет")
        self.geometry("1400x950")
        self.configure(fg_color="#FFFFFF")

        self.hgt_path = None
        self.points = []
        self.current_matrix = None
        self.map_extent = None

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Левая панель
        self.sidebar = ctk.CTkScrollableFrame(
            self, width=340, label_text="Параметры системы",
            fg_color="#F2F2F2", label_text_color="black"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Группы параметров
        self.geo_frame = self.create_group("1. Геометрия трассы")
        self.h1_entry = self.create_field(self.geo_frame, "Высота подвеса А1 (м):", "15")
        self.h2_entry = self.create_field(self.geo_frame, "Высота подвеса А2 (м):", "15")

        self.freq_frame = self.create_group("2. Частотные характеристики")
        self.freq_entry = self.create_field(self.freq_frame, "Рабочая частота f (МГц):", "2400")

        self.line_frame = self.create_group("3. Параметры линии")
        self.reliability_entry = self.create_field(self.line_frame, "Надежность линии (%):", "99.9")
        self.intervals_entry = self.create_field(self.line_frame, "Кол-во интервалов M:", "1")

        self.equip_frame = self.create_group("4. Приемо-передатчик")
        self.power_entry = self.create_field(self.equip_frame, "Мощность передатчика P (Вт):", "1.0")
        self.sensitivity_entry = self.create_field(self.equip_frame, "Чувствительность приемника P_мин (дБм):", "-90")
        self.feeder_loss_entry = self.create_field(self.equip_frame, "Затухание в фидере (дБ):", "3.0")

        self.ant_frame = self.create_group("5. Антенная система")
        self.ant_diam_entry = self.create_field(self.ant_frame, "Диаметр антенны d (м):", "0.6")

        self.surface_frame = self.create_group("6. Подстилающая поверхность")
        surface_types = [
            "Малопересеченная равнина, пойменные луга, солончаки",
            "Малопересеченная равнина, покрытая лесом",
            "Среднепересеченная открытая местность",
            "Среднепересеченная местность, покрытая лесом"
        ]
        self.surface_var = ctk.StringVar(value=surface_types[0])
        self.surface_menu = ctk.CTkOptionMenu(
            self.surface_frame, values=surface_types, variable=self.surface_var
        )
        self.surface_menu.pack(pady=5, padx=10, fill="x")

        ctk.CTkLabel(self.ant_frame, text="Конструкция антенны:", text_color="black").pack(pady=(5, 0))
        self.ant_type_var = ctk.StringVar(value="Однозеркальная (η=0.6)")
        self.ant_type_menu = ctk.CTkOptionMenu(
            self.ant_frame, values=["Однозеркальная (η=0.6)", "Двузеркальная (η=0.7)"],
            variable=self.ant_type_var
        )
        self.ant_type_menu.pack(pady=(0, 10), padx=10, fill="x")

        # Кнопки
        self.btn_load = ctk.CTkButton(self.sidebar, text="Загрузить карту .HGT", command=self.load_file)
        self.btn_load.pack(pady=10, padx=10, fill="x")

        self.btn_plot = ctk.CTkButton(self.sidebar, text="Построить профиль",
                                      command=self.show_profile_window, fg_color="#2c5d2c", hover_color="#1e401e")
        self.btn_plot.pack(pady=10, padx=10, fill="x")

        self.btn_clear = ctk.CTkButton(self.sidebar, text="Сбросить точки",
                                       command=self.clear_points, fg_color="#777777", hover_color="#555555")
        self.btn_clear.pack(pady=5, padx=10, fill="x")

        # Карта (справа)
        self.plot_frame = ctk.CTkFrame(self, fg_color="#FFFFFF")
        self.plot_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor='#F5F5F5')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#FFFFFF')
        self.ax.tick_params(colors='black', labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color('black')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)
        canvas_widget.configure(bg='#FFFFFF', highlightthickness=0)

        self.canvas.mpl_connect('button_press_event', self.on_map_click)

    def create_group(self, title):
        frame = ctk.CTkFrame(self.sidebar, fg_color="#FFFFFF", border_width=1, border_color="#DDDDDD")
        frame.pack(pady=10, padx=5, fill="x")
        ctk.CTkLabel(frame, text=title, font=("Arial", 13, "bold"), text_color="#1f538d").pack(pady=5)
        return frame

    def create_field(self, master, label_text, default_val):
        ctk.CTkLabel(master, text=label_text, anchor="w", text_color="black").pack(pady=(5, 0), padx=10, fill="x")
        entry = ctk.CTkEntry(master, fg_color="#F9F9F9", text_color="black", border_color="#CCCCCC")
        entry.insert(0, default_val)
        entry.pack(pady=(0, 10), padx=10, fill="x")
        return entry

    def load_file(self):
        path = fd.askopenfilename(filetypes=[("HGT files", "*.hgt")])
        if path:
            self.hgt_path = path
            self.current_matrix, self.map_extent = app_logic.load_hgt_matrix(path)
            self.points = []
            self.refresh_map()
            self.btn_load.configure(text="Карта загружена", fg_color="#1f538d")

    def refresh_map(self):
        if self.current_matrix is not None:
            self.ax.clear()
            self.ax.set_facecolor('#FFFFFF')
            self.ax.tick_params(colors='black')
            for spine in self.ax.spines.values():
                spine.set_color('black')

            self.ax.imshow(self.current_matrix, extent=self.map_extent, cmap='terrain', origin='upper')

            for p in self.points:
                self.ax.plot(p[1], p[0], 'ro', markersize=7, markeredgecolor='black', markeredgewidth=1)

            if len(self.points) == 2:
                lats, lons = zip(*self.points)
                self.ax.plot(lons, lats, 'r--', linewidth=2)

            self.canvas.draw()

    def on_map_click(self, event):
        if event.inaxes and self.current_matrix is not None:
            if len(self.points) < 2:
                self.points.append((event.ydata, event.xdata))
                self.refresh_map()

    def clear_points(self):
        self.points = []
        self.refresh_map()

    def show_profile_window(self):
        if len(self.points) < 2 or self.hgt_path is None:
            return

        dist, elev = app_logic.get_elevation_profile(self.hgt_path, self.points[0], self.points[1])
        total_dist = dist[-1]
        distance = app_logic.haversine(self.points[0], self.points[1])

        try:
            h1, h2 = float(self.h1_entry.get()), float(self.h2_entry.get())
            freq_mhz = float(self.freq_entry.get())
            reliability = float(self.reliability_entry.get())
            intervals = float(self.intervals_entry.get())
            power = float(self.power_entry.get())
            power_dbm = 10 * np.log10(power * 1000)  # перевод Вт -> дБм
            sensitivity = float(self.sensitivity_entry.get())
            feeder_loss = float(self.feeder_loss_entry.get())
            ant_diam = float(self.ant_diam_entry.get())
            ant_type = self.ant_type_var.get()
        except ValueError:
            h1, h2, freq_mhz = 15, 15, 2400
            reliability, intervals, power, sensitivity, feeder_loss, ant_diam = 99.9, 1.0, 1.0, -90, 3.0, 0.6
            ant_type = "Однозеркальная (η=0.6)"

        freq_ghz = freq_mhz / 1000.0
        wavelength = 0.3 / freq_ghz  # м
        wavelength_cm = wavelength * 100  # см

        ant_efficiency = 0.6 if "Однозеркальная" in ant_type else 0.7
        G_linear = (np.pi * ant_diam) ** 2 * ant_efficiency / (wavelength ** 2)
        G_dBi = 10 * np.log10(G_linear) if G_linear > 0 else -np.inf

        d_km = distance / 1000.0
        free_space_loss = 122 + 20 * np.log10(d_km / wavelength)

        refraction_loss = 0.0  # потери за счет рефракции (пока не рассчитываем)

        earth_arc = app_logic.get_earth_arc(dist)
        elev_curved = elev + earth_arc

        ground_start, ground_end = elev_curved[0], elev_curved[-1]
        ant_start, ant_end = ground_start + h1, ground_end + h2
        los_line = np.linspace(ant_start, ant_end, len(dist))
        f_radius = app_logic.get_fresnel_zone(dist, total_dist, freq_ghz)

        top = ctk.CTkToplevel(self)
        top.title("Технический профиль трассы")
        top.geometry("1100x600")
        top.configure(fg_color="#FFFFFF")

        fig_p = Figure(figsize=(8, 5), dpi=100, facecolor='#FFFFFF')
        ax_p = fig_p.add_subplot(111)
        ax_p.set_facecolor('#FCFCFC')
        ax_p.tick_params(colors='black')

        ax_p.fill_between(dist, earth_arc, -100, color='#ADD8E6', alpha=0.3, label='Кривизна Земли')
        ax_p.fill_between(dist, elev_curved, earth_arc, color='sienna', alpha=0.6, label='Рельеф')
        ax_p.fill_between(dist, los_line - f_radius, los_line + f_radius, color='yellow', alpha=0.3,
                          label='Зона Френеля')
        ax_p.plot(dist, los_line, 'b--', label='Линия LOS', lw=1.5)

        # Мачты
        ax_p.plot([dist[0], dist[0]], [ground_start, ant_start], color='#444444', lw=3)
        ax_p.plot(dist[0], ant_start, 'ko', markersize=6, markeredgecolor='white')
        ax_p.plot([dist[-1], dist[-1]], [ground_end, ant_end], color='#444444', lw=3)
        ax_p.plot(dist[-1], ant_end, 'ko', markersize=6, markeredgecolor='white')

        # Переменные
        d1 = d2 = H0 = H_g = T_i = l = h = Wp = None
        x_left = x_right = None

        clearances = los_line - elev_curved
        if np.min(clearances) >= 0:  # Полуоткрытый или открытый
            min_clearance_idx = np.argmin(clearances)
            x0 = dist[min_clearance_idx]
            y0 = elev_curved[min_clearance_idx]
            x1, y1 = dist[0], ant_start
            x2, y2 = dist[-1], ant_end
            dx = x2 - x1
            dy = y2 - y1
            dx2 = dx * dx
            dy2 = dy * dy
            if dx2 + dy2 > 0:
                t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx2 + dy2)
                t = max(0, min(1, t))
                x_proj = x1 + t * dx
                y_proj = y1 + t * dy

                d1 = x_proj
                d2 = total_dist - x_proj
                H0 = np.sqrt((wavelength * d1 * d2) / total_dist)
                R0 = 6370000.0
                K = 4 / 3
                H_geom = y_proj - y0 - (d1 * d2) / (2 * R0)
                delta_H = (d1 * d2) / (2 * R0) * (1 - 1 / K)
                H_g = H_geom + delta_H

                if H_g > 0:
                    if intervals > 0:
                        T_i = (100 - reliability) / intervals
                    else:
                        T_i = 0

                    if H_g >= H0:
                        # ----- ОТКРЫТЫЙ ИНТЕРВАЛ -----
                        h0_rel = H_g / H0
                        surface_text = self.surface_var.get()

                        # Выбор Φ по таблице 3.4
                        if wavelength_cm <= 30:
                            phi_table = {
                                "Малопересеченная равнина, пойменные луга, солончаки": 0.9,
                                "Малопересеченная равнина, покрытая лесом": 0.7,
                                "Среднепересеченная открытая местность": 0.5,
                                "Среднепересеченная местность, покрытая лесом": 0.3
                            }
                        else:
                            phi_table = {
                                "Малопересеченная равнина, пойменные луга, солончаки": 0.95,
                                "Малопересеченная равнина, покрытая лесом": 0.9,
                                "Среднепересеченная открытая местность": 0.7,
                                "Среднепересеченная местность, покрытая лесом": 0.6
                            }
                        phi = phi_table.get(surface_text, 0.8)

                        # ----- АВТОМАТИЧЕСКИЙ РАСЧЁТ D -----
                        # Пытаемся найти участок отражения (пересечения LOS-H0 с рельефом)
                        critical_line = los_line - H0
                        crosses = []
                        for i in range(len(dist) - 1):
                            diff1 = elev_curved[i] - critical_line[i]
                            diff2 = elev_curved[i + 1] - critical_line[i + 1]
                            if diff1 * diff2 < 0:
                                x1c, x2c = dist[i], dist[i + 1]
                                y1c, y2c = elev_curved[i], elev_curved[i + 1]
                                yc1, yc2 = critical_line[i], critical_line[i + 1]
                                denom = (y2c - y1c) - (yc2 - yc1)
                                if abs(denom) > 1e-9:
                                    t_cross = (yc1 - y1c) / denom
                                    x_cross = x1c + t_cross * (x2c - x1c)
                                    crosses.append(x_cross)

                        if len(crosses) >= 2:
                            crosses.sort()
                            # Находим пересечения, охватывающие точку минимума просвета x0
                            left_cross = None
                            right_cross = None
                            for xc in crosses:
                                if xc <= x0 and (left_cross is None or xc > left_cross):
                                    left_cross = xc
                                if xc >= x0 and (right_cross is None or xc < right_cross):
                                    right_cross = xc
                            if left_cross is not None and right_cross is not None and left_cross < right_cross:
                                l0 = right_cross - left_cross  # протяжённость участка отражения, м
                                # Находим максимальную высоту рельефа на [left_cross, right_cross]
                                mask = (dist >= left_cross) & (dist <= right_cross)
                                if np.any(mask):
                                    max_elev = np.max(elev_curved[mask])
                                    y_left_crit = np.interp(left_cross, dist, critical_line)
                                    y_right_crit = np.interp(right_cross, dist, critical_line)
                                    x_max = dist[mask][np.argmax(elev_curved[mask])]
                                    if right_cross - left_cross > 0:
                                        t_mn = (x_max - left_cross) / (right_cross - left_cross)
                                        y_mn = y_left_crit + t_mn * (y_right_crit - y_left_crit)
                                        delta_y = max_elev - y_mn  # высота хорды (стрелка прогиба), м
                                    else:
                                        delta_y = 0
                                else:
                                    l0, delta_y = 0, 0
                            else:
                                l0, delta_y = 0, 0
                        else:
                            l0, delta_y = 0, 0
                        # Расчёт радиуса кривизны a по формуле (3.14): a = l0^2 / (8 * Δy)
                        if l0 > 0 and delta_y > 0:
                            a = (l0 ** 2) / (8 * delta_y)  # м
                            # Ограничиваем разумными пределами (от 100 м до 100 000 км)
                            a = np.clip(a, 100, 100_000_000)
                        else:
                            a = 1e9  # большое значение -> плоская поверхность

                        # Расчёт коэффициента расходимости D по формуле (3.15)
                        R = total_dist
                        R1 = d1
                        H = H_g
                        H0_val = H0
                        if a > 0 and H0_val > 0 and R > 0:
                            term = (2 * R1 * (R - R1)) / (a * R) * (H / H0_val)
                            # Ограничиваем term, чтобы избежать ошибок
                            term = max(0, term)
                            D = 1.0 / np.sqrt(1 + term)
                        else:
                            D = 1.0

                        # Эффективный коэффициент отражения
                        # Если D < 0.95, учитываем расходимость
                        if D < 0.95:
                            phi3 = phi * D
                        else:
                            phi3 = phi

                        # Расчёт затухания по формуле (3.16)
                        cos_term = np.cos((np.pi / 3) * (h0_rel ** 2))
                        cos_term = np.clip(cos_term, -1.0, 1.0)
                        Wp = -10 * np.log10(1 + phi3 ** 2 - 2 * phi3 * cos_term)
                        if np.isnan(Wp) or Wp > 50:
                            Wp = 50.0
                        total_loss = free_space_loss + Wp + refraction_loss + 2 * feeder_loss
                        P_rx = power_dbm + 2 * G_dBi - total_loss
                        l = 0
                        h = 0
                        # ----- Визуализация для открытого интервала -----
                        if l0 > 0 and delta_y > 0 and left_cross is not None and right_cross is not None:
                            # Точки пересечения
                            y_left_crit = np.interp(left_cross, dist, critical_line)
                            y_right_crit = np.interp(right_cross, dist, critical_line)
                            ax_p.plot(left_cross, y_left_crit, 'bo', markersize=6, label='Границы участка отражения')
                            ax_p.plot(right_cross, y_right_crit, 'bo', markersize=6)

                            # Хорда l0 (зелёная линия)
                            ax_p.plot([left_cross, right_cross], [y_left_crit, y_right_crit], 'g-', linewidth=2,
                                      label=f'Хорда l₀ = {l0:.0f} м')

                            # Стрелка Δy (красная вертикаль от хорды до максимума рельефа)
                            # Находим координаты максимальной точки рельефа на [left_cross, right_cross]
                            mask = (dist >= left_cross) & (dist <= right_cross)
                            if np.any(mask):
                                max_idx = np.argmax(elev_curved[mask])
                                x_max = dist[mask][max_idx]
                                y_max = elev_curved[mask][max_idx]
                                # Вычисляем высоту хорды в точке x_max
                                y_chord = np.interp(x_max, [left_cross, right_cross], [y_left_crit, y_right_crit])
                                ax_p.plot([x_max, x_max], [y_chord, y_max], 'r-', linewidth=2,
                                          label=f'Δy = {delta_y:.1f} м')
                                ax_p.plot(x_max, y_max, 'ro', markersize=6, label='Вершина отражающего участка')

                            # Схематичная дуга радиуса a
                            # Рисуем полуокружность над хордой (центр на середине хорды, на расстоянии a от хорды)
                            center_x = (left_cross + right_cross) / 2
                            chord_half = l0 / 2
                            # Радиус a (в метрах)
                            if a < 1e8:  # не слишком большое
                                # Вычисляем центр окружности: он находится на перпендикуляре к хорде вверх на величину (a - Δy)
                                # Но для простоты нарисуем дугу с центром в середине хорды, радиусом a, углами от -α до α
                                # где α = arcsin(chord_half / a)
                                if a > chord_half:
                                    alpha = np.arcsin(chord_half / a)
                                    # Координаты дуги (верхняя полуокружность)
                                    theta = np.linspace(-alpha, alpha, 50)
                                    x_arc = center_x + a * np.sin(theta)
                                    y_arc = y_left_crit + (a - a * np.cos(theta))  # поднятие относительно концов хорды
                                    # Сдвигаем, чтобы концы дуги совпали с концами хорды
                                    # Более простой способ: центр окружности находится на расстоянии a от хорды по вертикали
                                    center_y = y_left_crit + a - np.sqrt(
                                        a ** 2 - chord_half ** 2)  # точный центр для дуги
                                    y_arc = center_y - a * np.cos(theta)
                                    ax_p.plot(x_arc, y_arc, 'm--', linewidth=1.5, alpha=0.7,
                                              label=f'Радиус a = {a / 1000:.1f} км')
                                    # Отметим центр окружности
                                    ax_p.plot(center_x, center_y, 'mx', markersize=5)

                    else:
                        # ----- ПОЛУОТКРЫТЫЙ ИНТЕРВАЛ -----
                        # Рисуем точку и перпендикуляр
                        ax_p.plot(x0, y0, 'ro', markersize=8, markeredgecolor='black', zorder=5,
                                  label='Ближайшая точка рельефа')
                        ax_p.plot([x0, x_proj], [y0, y_proj], 'g-', linewidth=2, label='Перпендикуляр к LOS')

                        critical_line = los_line - H0
                        # Поиск пересечений
                        crosses = []
                        for i in range(len(dist) - 1):
                            diff1 = elev_curved[i] - critical_line[i]
                            diff2 = elev_curved[i + 1] - critical_line[i + 1]
                            if diff1 * diff2 < 0:
                                x1c, x2c = dist[i], dist[i + 1]
                                y1c, y2c = elev_curved[i], elev_curved[i + 1]
                                yc1, yc2 = critical_line[i], critical_line[i + 1]
                                denom = (y2c - y1c) - (yc2 - yc1)
                                if abs(denom) > 1e-9:
                                    t_cross = (yc1 - y1c) / denom
                                    x_cross = x1c + t_cross * (x2c - x1c)
                                    crosses.append(x_cross)
                        if len(crosses) >= 2:
                            crosses.sort()
                            left_cross = None
                            right_cross = None
                            for xc in crosses:
                                if xc <= x0 and (left_cross is None or xc > left_cross):
                                    left_cross = xc
                                if xc >= x0 and (right_cross is None or xc < right_cross):
                                    right_cross = xc
                            if left_cross is not None and right_cross is not None and left_cross < right_cross:
                                x_left = left_cross
                                x_right = right_cross
                                l = x_right - x_left
                                mask = (dist >= x_left) & (dist <= x_right)
                                if np.any(mask):
                                    max_elev = np.max(elev_curved[mask])
                                    y_left_crit = np.interp(x_left, dist, critical_line)
                                    y_right_crit = np.interp(x_right, dist, critical_line)
                                    x_max = dist[mask][np.argmax(elev_curved[mask])]
                                    if x_right - x_left > 0:
                                        t_mn = (x_max - x_left) / (x_right - x_left)
                                        y_mn = y_left_crit + t_mn * (y_right_crit - y_left_crit)
                                        h = max_elev - y_mn
                                    else:
                                        h = 0
                                else:
                                    l, h = 0, 0
                            else:
                                l, h = 0, 0
                        else:
                            l, h = 0, 0

                        if l <= 0 or h <= 0:
                            Wp = 0.0
                            l = 0
                            h = 0
                        else:
                            p_rel = H_g / H0 if H0 > 0 else 0
                            if p_rel < 1:
                                Wp = 12 * (1 - p_rel) ** 2
                            else:
                                Wp = 0.0
                            total_loss = free_space_loss + Wp + refraction_loss + 2 * feeder_loss
                            P_rx = power_dbm + 2 * G_dBi - total_loss
                        # Визуализация для полуоткрытого интервала
                        ax_p.plot(dist, critical_line, 'k--', linewidth=1.5, alpha=0.7,
                                  label='LOS - H₀ (критический уровень)')
                        if l > 0 and h > 0 and x_left is not None and x_right is not None:
                            y_left_crit = np.interp(x_left, dist, critical_line)
                            y_right_crit = np.interp(x_right, dist, critical_line)
                            ax_p.plot(x_left, y_left_crit, 'bo', markersize=6, label='Точки пересечения')
                            ax_p.plot(x_right, y_right_crit, 'bo', markersize=6)
                            ax_p.plot([x_left, x_right], [y_left_crit, y_right_crit], 'g--', linewidth=1.5,
                                      label='Прямая mn')
                            ax_p.annotate('', xy=(x_left, y_left_crit - 5), xytext=(x_right, y_left_crit - 5),
                                          arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
                            ax_p.text((x_left + x_right) / 2, y_left_crit - 15, f'l = {l:.0f} м',
                                      ha='center', fontsize=8, color='blue')
                            y_mn_at_x0 = np.interp(x0, [x_left, x_right], [y_left_crit, y_right_crit])
                            ax_p.plot([x0, x0], [y_mn_at_x0, y0], 'r-', linewidth=2, label=f'h = {h:.1f} м')
                            ax_p.text(x0 + 5, (y_mn_at_x0 + y0) / 2, f'h = {h:.1f} м', fontsize=8, color='red',
                                      bbox=dict(facecolor='white', alpha=0.6))
                else:
                    ax_p.text(0.5, 0.5, "Интервал закрытый (LOS пересекает рельеф с учётом рефракции)",
                              transform=ax_p.transAxes, ha='center', fontsize=12, color='red')
        else:
            ax_p.text(0.5, 0.5, "Интервал закрытый (LOS пересекает рельеф)",
                      transform=ax_p.transAxes, ha='center', fontsize=12, color='red')

        # Оформление осей (без изменений)
        ax_p.set_xlim(0, total_dist)
        y_min = min(0, np.min(earth_arc))
        y_max = max(ant_start, ant_end, np.max(elev_curved)) * 1.15
        ax_p.set_ylim(y_min, y_max)
        ax_p.set_title(f"Профиль трассы (f = {freq_mhz} МГц)", color='black')
        ax_p.set_xlabel("Дистанция (м)")
        ax_p.set_ylabel("Высота (м)")
        ax_p.legend(loc='upper right', frameon=True, facecolor='white')
        ax_p.grid(True, alpha=0.3, color='gray')

        # Текстовая информация (без изменений)
        info_base = (
            f"Длина трассы: {distance / 1000:.2f} км\n"
            f"Высоты антенн: {h1} м / {h2} м\n"
            f"Рабочая частота: {freq_mhz} МГц\n"
            f"Длина волны: {wavelength:.3f} м ({wavelength_cm:.1f} см)\n"
            f"Коэфф. усиления антенны: {G_dBi:.1f} дБи\n"
            f"Потери в свободном пространстве: {free_space_loss:.1f} дБ\n"
            f"Надёжность: {reliability}%\n"
            f"Кол-во интервалов M: {intervals:.0f}\n"
            f"Мощность: {power} Вт\n"
            f"Чувствительность: {sensitivity} дБм\n"
            f"Затухание фидера: {feeder_loss} дБ\n"
            f"Антенна: {ant_type} (d={ant_diam} м)"
        )

        if d1 is not None and H_g is not None and H_g > 0:
            if H_g >= H0:
                h0_rel = H_g / H0
                surface_text = self.surface_var.get()
                info_extra = (
                    f"\nd1 = {d1:.0f} м, d2 = {d2:.0f} м\n"
                    f"Радиус зоны Френеля H0 = {H0:.2f} м\n"
                    f"Фактический просвет H(g) = {H_g:.2f} м\n"
                    f"Относительный просвет h0 = {h0_rel:.3f}\n"
                    f"Коэфф. перерыва связи T_i = {T_i:.4f} %\n"
                    f"Тип поверхности: {surface_text}\n"
                    f"Протяжённость участка отражения l0 = {l0:.0f} м\n"
                    f"Коэфф. расходимости D = {D:.4f}\n"
                    f"Коэфф. отражения Φ₃ = {phi3:.4f}\n"
                    f"Затухание на рельеф Wp = {Wp:.1f} дБ\n"
                    f"Суммарные потери: {total_loss:.1f} дБ\n"
                    f"Уровень сигнала на входе приёмника: {P_rx:.1f} дБм"
                )
            else:
                info_extra = (
                    f"\nd1 = {d1:.0f} м, d2 = {d2:.0f} м\n"
                    f"Радиус зоны Френеля H0 = {H0:.2f} м\n"
                    f"Фактический просвет H(g) = {H_g:.2f} м\n"
                    f"Коэфф. перерыва связи T_i = {T_i:.4f} %\n"
                    f"Затухание на рельеф Wp = {Wp:.1f} дБ\n"
                    f"Суммарные потери: {total_loss:.1f} дБ\n"
                    f"Уровень сигнала на входе приёмника: {P_rx:.1f} дБм"
                )
        elif d1 is not None and H_g is not None and H_g <= 0:
            info_extra = "\n(Интервал закрытый с учётом рефракции: H(g) <= 0)"
        else:
            info_extra = "\n(Интервал закрытый, дополнительные расчёты не выполнены)"

        info_text = info_base + info_extra
        ax_p.text(0.02, 0.98, info_text, transform=ax_p.transAxes,
                  fontsize=9, verticalalignment='top',
                  bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        canvas_p = FigureCanvasTkAgg(fig_p, master=top)
        canvas_p.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        canvas_p.get_tk_widget().configure(bg='#FFFFFF', highlightthickness=0)
        canvas_p.draw()
