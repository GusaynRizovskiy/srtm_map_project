# gui_module.py
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter.filedialog as fd
import tkinter.messagebox as mb
import numpy as np
import app_logic
import tkinter as tk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


def calculate_refraction_loss(Ti_percent, freq_ghz):
    """
    Затухание на рефракцию Wз, дБ.
    Для Ti >= 1% – основная интерполяция по графику.
    Для Ti < 1% – интерполяция между значениями при 1% и 0.05%.
    """
    if Ti_percent <= 0 or Ti_percent > 100:
        return 0.0
    Ti = max(0.05, min(50.0, Ti_percent))  # рабочий диапазон 0.05...50%

    def wz_at_1percent(f):
        f_ref = [0.2, 2.0, 6.0]
        A_ref = [-1.49, -1.91, -0.98]
        B_ref = [5.00, 8.45, 9.99]
        log_f = np.log10(f)
        log_f_ref = np.log10(f_ref)
        if f <= f_ref[0]:
            A, B = A_ref[0], B_ref[0]
        elif f >= f_ref[-1]:
            A, B = A_ref[-1], B_ref[-1]
        else:
            idx = 0
            while idx < len(f_ref) - 1 and f > f_ref[idx + 1]:
                idx += 1
            t = (log_f - log_f_ref[idx]) / (log_f_ref[idx + 1] - log_f_ref[idx])
            A = A_ref[idx] + t * (A_ref[idx + 1] - A_ref[idx])
            B = B_ref[idx] + t * (B_ref[idx + 1] - B_ref[idx])
        return A + B * 2.0

    f_tiny = np.array([0.1, 0.2, 0.4, 0.8, 2.0, 4.0, 6.0])
    wz_tiny = np.array([9.0, 14.0, 17.0, 21.0, 25.0, 28.0, 32.0])

    def wz_at_005percent(f):
        if f <= f_tiny[0]: return wz_tiny[0]
        if f >= f_tiny[-1]: return wz_tiny[-1]
        log_f = np.log10(f)
        log_f_tiny = np.log10(f_tiny)
        return np.interp(log_f, log_f_tiny, wz_tiny)

    if Ti >= 1.0:
        f_ref = [0.2, 2.0, 6.0]
        A_ref = [-1.49, -1.91, -0.98]
        B_ref = [5.00, 8.45, 9.99]
        log_f = np.log10(freq_ghz)
        log_f_ref = np.log10(f_ref)
        if freq_ghz <= f_ref[0]:
            A, B = A_ref[0], B_ref[0]
        elif freq_ghz >= f_ref[-1]:
            A, B = A_ref[-1], B_ref[-1]
        else:
            idx = 0
            while idx < len(f_ref) - 1 and freq_ghz > f_ref[idx + 1]:
                idx += 1
            t = (log_f - log_f_ref[idx]) / (log_f_ref[idx + 1] - log_f_ref[idx])
            A = A_ref[idx] + t * (A_ref[idx + 1] - A_ref[idx])
            B = B_ref[idx] + t * (B_ref[idx + 1] - B_ref[idx])
        Wz = A + B * np.log10(100.0 / Ti)
    else:
        wz_1 = wz_at_1percent(freq_ghz)
        wz_005 = wz_at_005percent(freq_ghz)
        log_Ti = np.log10(Ti)
        log_1 = np.log10(1.0)
        log_005 = np.log10(0.05)
        t = (log_Ti - log_005) / (log_1 - log_005)
        Wz = wz_005 + t * (wz_1 - wz_005)

    return min(max(Wz, 0.0), 50.0)


class RadioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Радиосвязь: Инженерный расчет")
        self.geometry("1400x950")
        self.configure(fg_color="#FFFFFF")

        self.raster_path = None
        self.points = []
        self.current_matrix = None
        self.map_extent = None

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkScrollableFrame(
            self, width=340, label_text="Параметры системы",
            fg_color="#F2F2F2", label_text_color="black"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.geo_frame = self.create_group("1. Геометрия трассы")
        self.h1_entry = self.create_field(self.geo_frame, "Высота подвеса А1 (м):", "15")
        self.h2_entry = self.create_field(self.geo_frame, "Высота подвеса А2 (м):", "15")

        self.coord_frame = self.create_group("Ручной ввод координат (градусы)")
        ctk.CTkLabel(self.coord_frame, text="Точка А1 (передатчик):", anchor="w", text_color="black").pack(pady=(5, 0),
                                                                                                           padx=10,
                                                                                                           fill="x")
        self.lat1_entry = self.create_field(self.coord_frame, "Широта (lat):", "")
        self.lon1_entry = self.create_field(self.coord_frame, "Долгота (lon):", "")
        ctk.CTkLabel(self.coord_frame, text="Точка А2 (приёмник):", anchor="w", text_color="black").pack(pady=(5, 0),
                                                                                                         padx=10,
                                                                                                         fill="x")
        self.lat2_entry = self.create_field(self.coord_frame, "Широта (lat):", "")
        self.lon2_entry = self.create_field(self.coord_frame, "Долгота (lon):", "")
        self.btn_set_coords = ctk.CTkButton(self.coord_frame, text="Установить точки",
                                            command=self.set_points_from_coords)
        self.btn_set_coords.pack(pady=10, padx=10, fill="x")

        self.freq_frame = self.create_group("2. Частотные характеристики")
        self.freq_entry = self.create_field(self.freq_frame, "Рабочая частота f (МГц):", "2400")

        self.line_frame = self.create_group("3. Параметры линии")
        self.reliability_entry = self.create_field(self.line_frame, "Надежность линии (%):", "99.9")
        self.intervals_entry = self.create_field(self.line_frame, "Кол-во интервалов M:", "1")

        self.equip_frame = self.create_group("4. Приемо-передатчик")
        self.power_entry = self.create_field(self.equip_frame, "Мощность передатчика P (дБм):", "1.0")
        self.sensitivity_entry = self.create_field(self.equip_frame, "Чувствительность приемника P_мин (дБм):", "-90")
        self.feeder_loss_entry = self.create_field(self.equip_frame, "Затухание в фидере (дБ):", "3.0")

        self.ant_frame = self.create_group("5. Антенная система")
        self.ant_diam_entry = self.create_field(self.ant_frame, "Диаметр антенны d (м):", "0.6")

        self.surface_frame = self.create_group("6. Подстилающая поверхность")
        surface_types = [
            "Малопересеченная равнина, пойменные луга, солончаки",
            "Малопересеченная равнина, покрытая лесом",
            "Среднепересеченная открытая местность",
            "Среднепересеченная местность, покрытая лесом",
            "Водная поверхность (море, озеро)"
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

        self.btn_load = ctk.CTkButton(self.sidebar, text="Загрузить карту", command=self.load_file)
        self.btn_load.pack(pady=10, padx=10, fill="x")

        self.btn_plot = ctk.CTkButton(self.sidebar, text="Построить профиль",
                                      command=self.show_profile_window, fg_color="#2c5d2c", hover_color="#1e401e")
        self.btn_plot.pack(pady=10, padx=10, fill="x")

        self.btn_clear = ctk.CTkButton(self.sidebar, text="Сбросить точки",
                                       command=self.clear_points, fg_color="#777777", hover_color="#555555")
        self.btn_clear.pack(pady=5, padx=10, fill="x")

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
        path = fd.askopenfilename(filetypes=[("Карты высот", "*.hgt *.tif *.tiff"), ("All files", "*.*")])
        if path:
            self.raster_path = path
            self.current_matrix, self.map_extent = app_logic.load_raster_matrix(path)
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
        self.lat1_entry.delete(0, tk.END)
        self.lon1_entry.delete(0, tk.END)
        self.lat2_entry.delete(0, tk.END)
        self.lon2_entry.delete(0, tk.END)
        self.refresh_map()

    def set_points_from_coords(self):
        if self.map_extent is None:
            mb.showerror("Ошибка", "Сначала загрузите карту")
            return
        try:
            lat1 = float(self.lat1_entry.get())
            lon1 = float(self.lon1_entry.get())
            lat2 = float(self.lat2_entry.get())
            lon2 = float(self.lon2_entry.get())
        except ValueError:
            mb.showerror("Ошибка", "Введите корректные числовые значения координат (градусы)")
            return

        left, right, bottom, top = self.map_extent
        if not (left <= lon1 <= right and bottom <= lat1 <= top):
            mb.showerror("Ошибка",
                         f"Точка А1 выходит за пределы карты.\nДопустимый диапазон:\nШирота: {bottom:.4f} ... {top:.4f}\nДолгота: {left:.4f} ... {right:.4f}")
            return
        if not (left <= lon2 <= right and bottom <= lat2 <= top):
            mb.showerror("Ошибка",
                         f"Точка А2 выходит за пределы карты.\nДопустимый диапазон:\nШирота: {bottom:.4f} ... {top:.4f}\nДолгота: {left:.4f} ... {right:.4f}")
            return

        self.points = [(lat1, lon1), (lat2, lon2)]
        self.refresh_map()

    def show_profile_window(self):
        if len(self.points) < 2 or self.raster_path is None:
            return

        dist, elev = app_logic.get_elevation_profile(self.raster_path, self.points[0], self.points[1])
        total_dist = dist[-1]
        distance = app_logic.haversine(self.points[0], self.points[1])

        try:
            h1, h2 = float(self.h1_entry.get()), float(self.h2_entry.get())
            freq_mhz = float(self.freq_entry.get())
            reliability = float(self.reliability_entry.get())
            intervals = float(self.intervals_entry.get())
            power = float(self.power_entry.get())
            sensitivity = -abs(float(self.sensitivity_entry.get()))
            feeder_loss = float(self.feeder_loss_entry.get())
            ant_diam = float(self.ant_diam_entry.get())
            ant_type = self.ant_type_var.get()
        except ValueError:
            h1, h2, freq_mhz = 15, 15, 2400
            reliability, intervals, power, sensitivity, feeder_loss, ant_diam = 99.9, 1.0, 1.0, -90, 3.0, 0.6
            ant_type = "Однозеркальная (η=0.6)"

        freq_ghz = freq_mhz / 1000.0
        wavelength = 0.3 / freq_ghz
        wavelength_cm = wavelength * 100

        ant_efficiency = 0.6 if "Однозеркальная" in ant_type else 0.7
        G_linear = (np.pi * ant_diam) ** 2 * ant_efficiency / (wavelength ** 2)
        G_dB = 10 * np.log10(G_linear) if G_linear > 0 else -np.inf

        d_km = distance / 1000.0
        if distance > 0:
            free_space_loss = 20 * np.log10((4 * 3.14 * distance) / wavelength)
        else:
            free_space_loss = 0
        refraction_loss = 0.0

        earth_arc = app_logic.get_earth_arc(dist)
        elev_curved = elev + earth_arc

        ground_start, ground_end = elev_curved[0], elev_curved[-1]
        ant_start, ant_end = ground_start + h1, ground_end + h2
        los_line = np.linspace(ant_start, ant_end, len(dist))
        f_radius = app_logic.get_fresnel_zone(dist, total_dist, freq_ghz)

        top = ctk.CTkToplevel(self)
        top.title("Технический профиль трассы")
        top.geometry("1500x700")
        top.configure(fg_color="#FFFFFF")

        main_frame = ctk.CTkFrame(top, fg_color="#FFFFFF")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ctk.CTkScrollableFrame(main_frame, width=420, fg_color="#F2F2F2", corner_radius=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        right_frame = ctk.CTkFrame(main_frame, fg_color="#FFFFFF")
        right_frame.grid(row=0, column=1, sticky="nsew")

        main_frame.grid_columnconfigure(0, weight=0)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        def insert_parameter_line(text_widget, line, empty_line_after=True):
            if ':' in line:
                param, value = line.split(':', 1)
                param += ':'
                value = value.strip()
            else:
                param, value = line, ''
            text_widget.insert("end", param, "normal")
            if value:
                text_widget.insert("end", " " + value, "bold")
            if empty_line_after:
                text_widget.insert("end", "\n\n")
            else:
                text_widget.insert("end", "\n")

        ctk.CTkLabel(left_frame, text="Исходные данные", font=("Segoe UI", 16, "bold")).pack(pady=(10, 5))
        text_initial = tk.Text(left_frame, wrap="word", font=("Segoe UI", 14),
                               bg="#F2F2F2", fg="black", bd=0, highlightthickness=0,
                               state="normal", height=25, takefocus=0)
        text_initial.pack(padx=10, pady=5, fill="both", expand=False)

        text_initial.bind("<MouseWheel>", lambda e: left_frame._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        text_initial.tag_configure("normal", font=("Segoe UI", 14))
        text_initial.tag_configure("bold", font=("Segoe UI", 14, "bold"))

        initial_lines = [
            f"Высота антенны А1: {h1} м",
            f"Высота антенны А2: {h2} м",
            f"Рабочая частота: {freq_mhz} МГц",
            f"Длина волны: {wavelength:.3f} м ({wavelength_cm:.1f} см)",
            f"Надёжность линии: {reliability} %",
            f"Кол-во интервалов M: {int(intervals)}",
            f"Мощность передатчика: {power} дБм",
            f"Чувствительность: {sensitivity} дБм",
            f"Затухание в фидере: {feeder_loss} дБ",
            f"Диаметр антенны D: {ant_diam} м",
            f"Тип антенны: {ant_type}",
            f"Подстилающая поверхность: {self.surface_var.get()}"
        ]

        for line in initial_lines:
            insert_parameter_line(text_initial, line, empty_line_after=True)
        text_initial.delete("end-2c", "end")
        text_initial.configure(state="disabled")

        ctk.CTkLabel(left_frame, text="Результаты расчёта", font=("Segoe UI", 16, "bold")).pack(pady=(20, 5))
        text_results = tk.Text(left_frame, wrap="word", font=("Segoe UI", 14),
                               bg="#F2F2F2", fg="black", bd=0, highlightthickness=0,
                               state="normal", height=40, takefocus=0)
        text_results.pack(padx=10, pady=5, fill="both", expand=True)

        text_results.bind("<MouseWheel>", lambda e: left_frame._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        text_results.tag_configure("normal", font=("Segoe UI", 14))
        text_results.tag_configure("bold", font=("Segoe UI", 14, "bold"))

        def update_results_text(lines_list):
            print(f"P_tx: {power}, G: {G_dB}, FSPL: {free_space_loss}, Wp: {Wp}, P_rx: {P_prm_dbm}")
            text_results.configure(state="normal")
            text_results.delete("1.0", "end")
            for i, line in enumerate(lines_list):
                empty_line = (i != len(lines_list) - 1)
                insert_parameter_line(text_results, line, empty_line_after=empty_line)
            text_results.configure(state="disabled")

        fig_p = Figure(figsize=(8, 5), dpi=100, facecolor='#FFFFFF')
        ax_p = fig_p.add_subplot(111)
        ax_p.set_facecolor('#FCFCFC')
        ax_p.tick_params(colors='black')

        ax_p.fill_between(dist, earth_arc, -100, color='#ADD8E6', alpha=0.3, label='Кривизна Земли')
        ax_p.fill_between(dist, elev_curved, earth_arc, color='sienna', alpha=0.6, label='Рельеф')
        ax_p.fill_between(dist, los_line - f_radius, los_line + f_radius, color='yellow', alpha=0.3,
                          label='Зона Френеля')
        ax_p.plot(dist, los_line, 'b--', label='Линия LOS', lw=1.5)

        ax_p.plot([dist[0], dist[0]], [ground_start, ant_start], color='#444444', lw=3, label='Мачты')
        ax_p.plot(dist[0], ant_start, 'ko', markersize=6, markeredgecolor='white')
        ax_p.plot([dist[-1], dist[-1]], [ground_end, ant_end], color='#444444', lw=3)
        ax_p.plot(dist[-1], ant_end, 'ko', markersize=6, markeredgecolor='white')

        ax_p.text(0.98, 0.98, f'Длина интервала: {total_dist:.0f} м ({total_dist / 1000:.2f} км)',
                  transform=ax_p.transAxes, ha='right', va='top', fontsize=10,
                  bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        clearances = los_line - elev_curved

        # Инициализируем базовые переменные дефолтными значениями на случай идеального интервала
        d1 = total_dist / 2.0
        d2 = total_dist / 2.0
        H0 = np.sqrt((wavelength * d1 * d2) / total_dist) if total_dist > 0 else 0.0

        # Индексы и координаты для середины трассы по умолчанию
        mid_idx = len(dist) // 2
        x0 = dist[mid_idx]
        y0 = elev_curved[mid_idx]

        x1, y1 = dist[0], ant_start
        x2, y2 = dist[-1], ant_end
        dx = x2 - x1
        dy = y2 - y1
        dx2 = dx * dx
        dy2 = dy * dy

        if dx2 + dy2 > 0:
            # Ищем критическую точку по минимальному относительному просвету (clearance / f_radius)
            with np.errstate(divide='ignore', invalid='ignore'):
                relative_clearances = clearances / f_radius

            # На краях трассы (мачты), где f_radius == 0, получаем NaN или Inf.
            # Заменяем их на бесконечность, чтобы np.argmin гарантированно их игнорировал.
            relative_clearances[np.isnan(relative_clearances) | np.isinf(relative_clearances)] = np.inf

            min_clearance_idx = np.argmin(relative_clearances)
            x0_real = dist[min_clearance_idx]
            y0_real = elev_curved[min_clearance_idx]

            t = ((x0_real - x1) * dx + (y0_real - y1) * dy) / (dx2 + dy2)
            t = max(0, min(1, t))
            x_proj_real = x1 + t * dx
            y_proj_real = y1 + t * dy

            H_geom = y_proj_real - y0_real

            # Если интервал открытый (светлый)
            if np.min(clearances) >= 0:
                x0 = x0_real
                y0 = y0_real
                x_proj = x_proj_real
                y_proj = y_proj_real

                d1 = x_proj
                d2 = total_dist - x_proj
                if d1 <= 0: d1 = 0.1
                if d2 <= 0: d2 = 0.1

                H0 = np.sqrt((wavelength * d1 * d2) / total_dist)
                R0 = 6370000.0
                K = 4 / 3
                delta_H = (d1 * d2) / (2 * R0) * (1 - 1 / K)
                H_g = H_geom + delta_H

                # Расчет надежности и рефракции
                if intervals > 0:
                    T_i = (100 - reliability) / intervals
                else:
                    T_i = 0
                refraction_loss = calculate_refraction_loss(T_i, freq_ghz)

                # Поиск участка отражения l0
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

                R1 = d1
                H = H_g
                if a > 0 and H0 > 0 and total_dist > 0:
                    term = (2 * R1 * (total_dist - R1)) / (a * total_dist) * (H / H0)
                    term = max(0, term)
                    D = 1.0 / np.sqrt(1 + term)
                else:
                    D = 1.0

                surface_text = self.surface_var.get()
                if wavelength_cm <= 30:
                    phi_table = {
                        "Малопересеченная равнина, пойменные луга, солончаки": 0.9,
                        "Малопересеченная равнина, покрытая лесом": 0.7,
                        "Среднепересеченная открытая местность": 0.5,
                        "Среднепересеченная местность, покрытая лесом": 0.3,
                        "Водная поверхность (море, озеро)": 1.0
                    }
                else:
                    phi_table = {
                        "Малопересеченная равнина, пойменные луга, солончаки": 0.95,
                        "Малопересеченная равнина, покрытая лесом": 0.9,
                        "Среднепересеченная открытая местность": 0.7,
                        "Среднепересеченная местность, покрытая лесом": 0.6,
                        "Водная поверхность (море, озеро)": 1.0
                    }
                phi = phi_table.get(surface_text, 0.8)
                phi3 = phi * D if D < 0.95 else phi

                h0_rel = H_g / H0 if H0 > 0 else 1.0
                cos_term = np.cos((np.pi / 3) * (h0_rel ** 2))
                cos_term = np.clip(cos_term, -1.0, 1.0)
                Wp = -10 * np.log10(1 + phi3 ** 2 - 2 * phi3 * cos_term)
                if np.isnan(Wp) or Wp > 50:
                    Wp = 50.0
                if Wp < 0: Wp = 0.0

                total_loss = free_space_loss + Wp + refraction_loss + 2 * feeder_loss
                P_prm_dbm = power + G_dB + G_dB - total_loss
                fade_margin = P_prm_dbm - sensitivity
                status = "ПРИГОДЕН" if fade_margin >= 0 else "НЕ ПРИГОДЕН"

                result_lines = [
                    f"Длина интервала: {total_dist:.0f} м ({total_dist / 1000:.2f} км)",
                    f"Длина волны: {wavelength:.3f} м ({wavelength_cm:.1f} см)",
                    f"Расстояние от передатчика до критической точки d1: {d1:.0f} м",
                    f"Расстояние от приемника до критической точки d2: {d2:.0f} м",
                    f"Коэффициент усиления антенны G: {G_dB:.1f} дБ",
                    f"Радиус зоны Френеля H0: {H0:.2f} м",
                    f"Фактический просвет H(g): {H_g:.2f} м",
                    f"Относительный просвет h0: {h0_rel:.3f}",
                    f"Коэфф. перерыва связи T_i: {T_i:.4f} %",
                    f"Тип поверхности: {surface_text}",
                    f"Протяжённость участка отражения l0: {l0:.0f} м",
                    f"Коэфф. расходимости D: {D:.4f}",
                    f"Коэфф. отражения Φ₃: {phi3:.4f}",
                    f"Затухание в свободном пространстве Wсв: {free_space_loss:.1f} дБ",
                    f"Затухание на рефракцию Wзам: {refraction_loss:.1f} дБ",
                    f"Затухание на рельеф Wрель: {Wp:.1f} дБ",
                    f"Суммарные потери Wсум (Wсв + Wзам + Wрель + фидер): {total_loss:.1f} дБ",
                    f"Мощность на входе приёмника Pпрм: {P_prm_dbm:.1f} дБм",
                    f"Запас на замирание M: {fade_margin:.1f} дБ",
                    f"Статус интервала: {status}"
                ]
                update_results_text(result_lines)

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
                        ax_p.plot([x_max, x_max], [y_chord, y_max], 'r-', linewidth=2, label=f'Δy = {delta_y:.1f} м')
                        ax_p.plot(x_max, y_max, 'ro', markersize=6, label='Вершина отражающего участка')

            else:
                # Если интервал ЗАКРЫТЫЙ (LOS пересекает рельеф)
                x0 = x0_real
                y0 = y0_real
                x_proj = x_proj_real
                y_proj = y_proj_real

                d1 = x_proj
                d2 = total_dist - x_proj
                if d1 <= 0: d1 = 0.1
                if d2 <= 0: d2 = 0.1

                H0 = np.sqrt((wavelength * d1 * d2) / total_dist)
                H_geom = y_proj - y0

                if intervals > 0:
                    T_i = (100 - reliability) / intervals
                else:
                    T_i = 0
                refraction_loss = calculate_refraction_loss(T_i, freq_ghz)

                # Расчет протяженности препятствия l и высоты h
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
                l = 0
                h = 0
                left_cross = right_cross = None

                if len(crosses) >= 2:
                    crosses.sort()
                    for xc in crosses:
                        if xc <= x0 and (left_cross is None or xc > left_cross):
                            left_cross = xc
                        if xc >= x0 and (right_cross is None or xc < right_cross):
                            right_cross = xc
                    if left_cross is not None and right_cross is not None:
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

                if l <= 0: l = total_dist
                if h <= 0: h = 0.01

                if H0 > 0:
                    p_rel = H_geom / H0
                    Wp = 12 * (1 - p_rel) ** 2
                else:
                    Wp = 20.0

                Wp = np.clip(Wp, 6.0, 40.0)

                total_loss = free_space_loss + Wp + refraction_loss + 2 * feeder_loss
                P_prm_dbm = power + G_dB + G_dB - total_loss
                fade_margin = P_prm_dbm - sensitivity
                status = "ПРИГОДЕН" if fade_margin >= 0 else "НЕ ПРИГОДЕН"

                result_lines = [
                    f"Интервал закрытый (LOS пересекает рельеф)",
                    f"Длина интервала: {total_dist:.0f} м ({total_dist / 1000:.2f} км)",
                    f"Длина волны: {wavelength:.3f} м ({wavelength_cm:.1f} см)",
                    f"Расстояние от передатчика до препятствия d1: {d1:.0f} м",
                    f"Расстояние от приёмника до препятствия d2: {d2:.0f} м",
                    f"Радиус зоны Френеля H0: {H0:.2f} м",
                    f"Геометрический просвет H(geom): {H_geom:.2f} м",
                    f"Коэфф. перерыва связи T_i: {T_i:.4f} %",
                    f"Протяжённость препятствия l: {l:.0f} м",
                    f"Высота препятствия h: {h:.1f} м",
                    f"Затухание в свободном пространстве Wсв: {free_space_loss:.1f} дБ",
                    f"Затухание на рефракцию Wзам: {refraction_loss:.1f} дБ",
                    f"Затухание на рельеф Wрель: {Wp:.1f} дБ",
                    f"Суммарные потери Wсум (Wсв + Wзам + Wрель + фидер): {total_loss:.1f} дБ",
                    f"Мощность на входе приёмника Pпрм: {P_prm_dbm:.1f} дБм",
                    f"Запас на замирание M: {fade_margin:.1f} дБ",
                    f"Статус интервала: {status}"
                ]
                update_results_text(result_lines)

                ax_p.plot(x0, y0, 'ro', markersize=8, markeredgecolor='black', zorder=5,
                          label='Критическая точка рельефа')
                ax_p.plot([x0, x_proj], [y0, y_proj], 'g-', linewidth=2, label='Перпендикуляр к LOS')
                ax_p.plot(dist, critical_line, 'k--', linewidth=1.5, alpha=0.7, label='LOS - H₀ (критический уровень)')

        ax_p.set_xlim(0, total_dist)
        y_min = min(0, np.min(earth_arc))
        y_max = max(ant_start, ant_end, np.max(elev_curved)) * 1.15
        ax_p.set_ylim(y_min, y_max)
        ax_p.set_title(f"Профиль трассы (f = {freq_mhz} МГц)", color='black')
        ax_p.set_xlabel("Дистанция (м)")
        ax_p.set_ylabel("Высота (м)")

        ax_p.legend(loc='best', frameon=True, facecolor='white', framealpha=0.7, fontsize=10, draggable=True)
        ax_p.grid(True, alpha=0.3, color='gray')

        canvas_p = FigureCanvasTkAgg(fig_p, master=right_frame)
        canvas_p.get_tk_widget().pack(fill="both", expand=True)
        canvas_p.draw()