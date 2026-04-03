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
        refraction_loss = 0.0

        earth_arc = app_logic.get_earth_arc(dist)
        elev_curved = elev + earth_arc

        ground_start, ground_end = elev_curved[0], elev_curved[-1]
        ant_start, ant_end = ground_start + h1, ground_end + h2
        los_line = np.linspace(ant_start, ant_end, len(dist))
        f_radius = app_logic.get_fresnel_zone(dist, total_dist, freq_ghz)

        # --- Окно с левой панелью и графиком ---
        top = ctk.CTkToplevel(self)
        top.title("Технический профиль трассы")
        top.geometry("1500x700")
        top.configure(fg_color="#FFFFFF")

        main_frame = ctk.CTkFrame(top, fg_color="#FFFFFF")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Левая панель (scrollable)
        left_frame = ctk.CTkScrollableFrame(main_frame, width=360, fg_color="#F2F2F2", corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Правая область для графика
        right_frame = ctk.CTkFrame(main_frame, fg_color="#FFFFFF")
        right_frame.grid(row=0, column=1, sticky="nsew")

        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Шрифты
        text_font = ("Segoe UI", 13)
        bold_font = ("Segoe UI", 14, "bold")

        # --- Исходные данные ---
        ctk.CTkLabel(left_frame, text="Исходные данные", font=bold_font).pack(pady=(10, 5))
        left_text = (
            f"Высота антенны А1: {h1} м\n"
            f"Высота антенны А2: {h2} м\n"
            f"Рабочая частота: {freq_mhz} МГц\n"
            f"Длина волны: {wavelength:.3f} м ({wavelength_cm:.1f} см)\n"
            f"Надёжность линии: {reliability} %\n"
            f"Кол-во интервалов M: {int(intervals)}\n"
            f"Мощность передатчика: {power} Вт\n"
            f"Чувствительность: {sensitivity} дБм\n"
            f"Затухание в фидере: {feeder_loss} дБ\n"
            f"Диаметр антенны: {ant_diam} м\n"
            f"Тип антенны: {ant_type}\n"
            f"Подстилающая поверхность: {self.surface_var.get()}"
        )
        ctk.CTkLabel(left_frame, text=left_text, justify="left", font=text_font, text_color="black",
                     wraplength=340).pack(padx=10, pady=5, anchor="nw")

        ctk.CTkLabel(left_frame, text="", height=10).pack()
        ctk.CTkLabel(left_frame, text="Результаты расчёта", font=bold_font).pack(pady=(10, 5))
        results_label = ctk.CTkLabel(left_frame, text="", justify="left", font=text_font, text_color="black",
                                     wraplength=340)
        results_label.pack(padx=10, pady=5, anchor="nw")

        # --- График ---
        fig_p = Figure(figsize=(8, 5), dpi=100, facecolor='#FFFFFF')
        ax_p = fig_p.add_subplot(111)
        ax_p.set_facecolor('#FCFCFC')
        ax_p.tick_params(colors='black')

        ax_p.fill_between(dist, earth_arc, -100, color='#ADD8E6', alpha=0.3, label='Кривизна Земли')
        ax_p.fill_between(dist, elev_curved, earth_arc, color='sienna', alpha=0.6, label='Рельеф')
        ax_p.fill_between(dist, los_line - f_radius, los_line + f_radius, color='yellow', alpha=0.3,
                          label='Зона Френеля')
        ax_p.plot(dist, los_line, 'b--', label='Линия LOS', lw=1.5)

        # Мачты – добавлена метка для отображения в легенде
        ax_p.plot([dist[0], dist[0]], [ground_start, ant_start], color='#444444', lw=3, label='Мачты')
        ax_p.plot(dist[0], ant_start, 'ko', markersize=6, markeredgecolor='white')
        ax_p.plot([dist[-1], dist[-1]], [ground_end, ant_end], color='#444444', lw=3)
        ax_p.plot(dist[-1], ant_end, 'ko', markersize=6, markeredgecolor='white')

        # --- Анализ интервала (полностью сохранён) ---
        clearances = los_line - elev_curved
        if np.min(clearances) >= 0:  # LOS не пересекает рельеф -> открытый или полуоткрытый
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
                # Геометрический просвет (без учёта рефракции)
                H_geom = y_proj - y0
                # Поправка на рефракцию
                delta_H = (d1 * d2) / (2 * R0) * (1 - 1 / K)
                H_g = H_geom + delta_H

                if intervals > 0:
                    T_i = (100 - reliability) / intervals
                else:
                    T_i = 0

                # Определяем тип интервала по эффективному просвету H_g
                if H_g >= H0:
                    # ========== ОТКРЫТЫЙ ИНТЕРВАЛ ==========
                    h0_rel = H_g / H0
                    surface_text = self.surface_var.get()

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

                    # Поиск участка отражения (пересечения LOS-H0 с рельефом)
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
                    l0 = 0
                    delta_y = 0
                    left_cross = right_cross = None
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
                            l0 = right_cross - left_cross
                            mask = (dist >= left_cross) & (dist <= right_cross)
                            if np.any(mask):
                                max_elev = np.max(elev_curved[mask])
                                y_left_crit = np.interp(left_cross, dist, critical_line)
                                y_right_crit = np.interp(right_cross, dist, critical_line)
                                x_max = dist[mask][np.argmax(elev_curved[mask])]
                                if l0 > 0:
                                    t_mn = (x_max - left_cross) / l0
                                    y_mn = y_left_crit + t_mn * (y_right_crit - y_left_crit)
                                    delta_y = max_elev - y_mn
                    if l0 > 0 and delta_y > 0:
                        a = (l0 ** 2) / (8 * delta_y)
                        a = np.clip(a, 100, 100_000_000)
                    else:
                        a = 1e9

                    R = total_dist
                    R1 = d1
                    H = H_g
                    if a > 0 and H0 > 0 and R > 0:
                        term = (2 * R1 * (R - R1)) / (a * R) * (H / H0)
                        term = max(0, term)
                        D = 1.0 / np.sqrt(1 + term)
                    else:
                        D = 1.0

                    phi3 = phi * D if D < 0.95 else phi

                    cos_term = np.cos((np.pi / 3) * (h0_rel ** 2))
                    cos_term = np.clip(cos_term, -1.0, 1.0)
                    Wp = -10 * np.log10(1 + phi3 ** 2 - 2 * phi3 * cos_term)
                    if np.isnan(Wp) or Wp > 50:
                        Wp = 50.0

                    total_loss = free_space_loss + Wp + refraction_loss + 2 * feeder_loss
                    P_tx_dbm = 10 * np.log10(power * 1000)
                    P_prm_dbm = P_tx_dbm + G_dBi + G_dBi - total_loss
                    status = "ПРИГОДЕН" if P_prm_dbm >= sensitivity else "НЕ ПРИГОДЕН"

                    result_text = (
                        f"d1 = {d1:.0f} м\nd2 = {d2:.0f} м\n"
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
                        f"Мощность на входе приёмника: {P_prm_dbm:.1f} дБм\n"
                        f"Статус интервала: {status}"
                    )
                    results_label.configure(text=result_text)

                    # Визуализация для открытого интервала (если есть отражающий участок)
                    if l0 > 0 and delta_y > 0 and left_cross is not None and right_cross is not None:
                        y_left_crit = np.interp(left_cross, dist, critical_line)
                        y_right_crit = np.interp(right_cross, dist, critical_line)
                        ax_p.plot(left_cross, y_left_crit, 'bo', markersize=6, label='Границы участка отражения')
                        ax_p.plot(right_cross, y_right_crit, 'bo', markersize=6)
                        ax_p.plot([left_cross, right_cross], [y_left_crit, y_right_crit], 'g-', linewidth=2,
                                  label=f'Хорда l₀ = {l0:.0f} м')
                        mask = (dist >= left_cross) & (dist <= right_cross)
                        if np.any(mask):
                            max_idx = np.argmax(elev_curved[mask])
                            x_max = dist[mask][max_idx]
                            y_max = elev_curved[mask][max_idx]
                            y_chord = np.interp(x_max, [left_cross, right_cross], [y_left_crit, y_right_crit])
                            ax_p.plot([x_max, x_max], [y_chord, y_max], 'r-', linewidth=2,
                                      label=f'Δy = {delta_y:.1f} м')
                            ax_p.plot(x_max, y_max, 'ro', markersize=6, label='Вершина отражающего участка')
                        if a < 5e5:
                            center_x = (left_cross + right_cross) / 2
                            chord_half = l0 / 2
                            if a > chord_half:
                                alpha = np.arcsin(chord_half / a)
                                theta = np.linspace(-alpha, alpha, 50)
                                center_y = y_left_crit + a - np.sqrt(a ** 2 - chord_half ** 2)
                                x_arc = center_x + a * np.sin(theta)
                                y_arc = center_y - a * np.cos(theta)
                                ax_p.plot(x_arc, y_arc, 'm--', linewidth=1.5, alpha=0.7,
                                          label=f'Радиус a = {a / 1000:.1f} км')
                                ax_p.plot(center_x, center_y, 'mx', markersize=5)

                else:
                    # ========== ПОЛУОТКРЫТЫЙ ИНТЕРВАЛ ==========
                    # Рисуем перпендикуляр и точку
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

                    l = 0
                    h = 0
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
                            l = right_cross - left_cross
                            mask = (dist >= left_cross) & (dist <= right_cross)
                            if np.any(mask):
                                max_elev = np.max(elev_curved[mask])
                                y_left_crit = np.interp(left_cross, dist, critical_line)
                                y_right_crit = np.interp(right_cross, dist, critical_line)
                                x_max = dist[mask][np.argmax(elev_curved[mask])]
                                if l > 0:
                                    t_mn = (x_max - left_cross) / l
                                    y_mn = y_left_crit + t_mn * (y_right_crit - y_left_crit)
                                    h = max_elev - y_mn

                    if l <= 0 or h <= 0:
                        Wp = 0.0
                        l = 0
                        h = 0
                    else:
                        p_rel = H_geom / H0 if H0 > 0 else 0
                        if p_rel < 1:
                            Wp = 12 * (1 - p_rel) ** 2
                        else:
                            Wp = 0.0

                    total_loss = free_space_loss + Wp + refraction_loss + 2 * feeder_loss
                    P_tx_dbm = 10 * np.log10(power * 1000)
                    P_prm_dbm = P_tx_dbm + G_dBi + G_dBi - total_loss
                    status = "ПРИГОДЕН" if P_prm_dbm >= sensitivity else "НЕ ПРИГОДЕН"

                    result_text = (
                        f"Расстояние от передатчика до препятствия d1 = {d1:.0f}м\n"
                        f"Расстояние от приемника до препятствия d2 = {d2:.0f}м\n"
                        f"Радиус зоны Френеля H0 = {H0:.2f} м\n"
                        f"Геометрический просвет H(geom) = {H_geom:.2f} м\n"
                        f"Коэфф. перерыва связи T_i = {T_i:.4f} %\n"
                        f"Протяжённость препятствия l = {l:.0f} м\n"
                        f"Высота препятствия h = {h:.1f} м\n"
                        f"Затухание на рельеф Wp = {Wp:.1f} дБ\n"
                        f"Суммарные потери: {total_loss:.1f} дБ\n"
                        f"Мощность на входе приёмника: {P_prm_dbm:.1f} дБм\n"
                        f"Статус интервала: {status}"
                    )
                    results_label.configure(text=result_text)

                    # Визуализация для полуоткрытого интервала
                    ax_p.plot(dist, critical_line, 'k--', linewidth=1.5, alpha=0.7,
                              label='LOS - H₀ (критический уровень)')
                    if l > 0 and h > 0 and left_cross is not None and right_cross is not None:
                        y_left_crit = np.interp(left_cross, dist, critical_line)
                        y_right_crit = np.interp(right_cross, dist, critical_line)
                        ax_p.plot(left_cross, y_left_crit, 'bo', markersize=6, label='Точки пересечения')
                        ax_p.plot(right_cross, y_right_crit, 'bo', markersize=6)
                        ax_p.plot([left_cross, right_cross], [y_left_crit, y_right_crit], 'g--', linewidth=1.5,
                                  label='Прямая mn')
                        ax_p.annotate('', xy=(left_cross, y_left_crit - 5), xytext=(right_cross, y_left_crit - 5),
                                      arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
                        ax_p.text((left_cross + right_cross) / 2, y_left_crit - 15, f'l = {l:.0f} м',
                                  ha='center', fontsize=8, color='blue')
                        y_mn_at_x0 = np.interp(x0, [left_cross, right_cross], [y_left_crit, y_right_crit])
                        ax_p.plot([x0, x0], [y_mn_at_x0, y0], 'r-', linewidth=2, label=f'h = {h:.1f} м')
                        ax_p.text(x0 + 5, (y_mn_at_x0 + y0) / 2, f'h = {h:.1f} м', fontsize=8, color='red',
                                  bbox=dict(facecolor='white', alpha=0.6))
        else:
            results_label.configure(text="Интервал закрытый (LOS пересекает рельеф)")

        # --- Оформление графика (изменена только легенда) ---
        ax_p.set_xlim(0, total_dist)
        y_min = min(0, np.min(earth_arc))
        y_max = max(ant_start, ant_end, np.max(elev_curved)) * 1.15
        ax_p.set_ylim(y_min, y_max)
        ax_p.set_title(f"Профиль трассы (f = {freq_mhz} МГц)", color='black')
        ax_p.set_xlabel("Дистанция (м)")
        ax_p.set_ylabel("Высота (м)")

        # Исправленная легенда: автоматический выбор места, полупрозрачность, возможность перетаскивания
        ax_p.legend(loc='best', frameon=True, facecolor='white', framealpha=0.7, fontsize=10, draggable=True)

        ax_p.grid(True, alpha=0.3, color='gray')

        # --- Встраивание графика ---
        canvas_p = FigureCanvasTkAgg(fig_p, master=right_frame)
        canvas_p.get_tk_widget().pack(fill="both", expand=True)
        canvas_p.draw()