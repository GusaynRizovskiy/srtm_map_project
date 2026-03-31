import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter.filedialog as fd
import numpy as np
import app_logic

# Устанавливаем СВЕТЛУЮ тему
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class RadioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Радиосвязь: Инженерный расчет")
        self.geometry("1400x950")

        # Цвет фона самого окна
        self.configure(fg_color="#FFFFFF")

        self.hgt_path = None
        self.points = []
        self.current_matrix = None
        self.map_extent = None

        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Левая панель (светло-серый фон для контраста)
        self.sidebar = ctk.CTkScrollableFrame(
            self,
            width=340,
            label_text="Параметры системы",
            fg_color="#F2F2F2",
            label_text_color="black"
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # --- ГРУППЫ ПАРАМЕТРОВ ---
        self.geo_frame = self.create_group("1. Геометрия трассы")
        self.h1_entry = self.create_field(self.geo_frame, "Высота подвеса А1 (м):", "15")
        self.h2_entry = self.create_field(self.geo_frame, "Высота подвеса А2 (м):", "15")

        self.freq_frame = self.create_group("2. Частотные характеристики")
        self.f_frenel_entry = self.create_field(self.freq_frame, "Частота для зоны Френеля (ГГц):", "2.4")
        self.f_max_entry = self.create_field(self.freq_frame, "Макс. рабочая частота f (МГц):", "2400")

        self.line_frame = self.create_group("3. Параметры линии")
        self.reliability_entry = self.create_field(self.line_frame, "Надежность линии (%):", "99.9")
        self.intervals_entry = self.create_field(self.line_frame, "Кол-во интервалов M:", "1")

        self.equip_frame = self.create_group("4. Приемо-передатчик")
        self.power_entry = self.create_field(self.equip_frame, "Мощность передатчика P (Вт):", "1.0")
        self.sensitivity_entry = self.create_field(self.equip_frame, "Чувствительность приемника P_мин (дБм):", "-90")
        self.feeder_loss_entry = self.create_field(self.equip_frame, "Затухание в фидере (дБ):", "3.0")

        self.ant_frame = self.create_group("5. Антенная система")
        self.ant_diam_entry = self.create_field(self.ant_frame, "Диаметр антенны d (м):", "0.6")

        ctk.CTkLabel(self.ant_frame, text="Конструкция антенны:", text_color="black").pack(pady=(5, 0))
        self.ant_type_var = ctk.StringVar(value="Однозеркальная (η=0.6)")
        self.ant_type_menu = ctk.CTkOptionMenu(
            self.ant_frame,
            values=["Однозеркальная (η=0.6)", "Двузеркальная (η=0.7)"],
            variable=self.ant_type_var
        )
        self.ant_type_menu.pack(pady=(0, 10), padx=10, fill="x")

        # Кнопки
        self.btn_load = ctk.CTkButton(self.sidebar, text="Загрузить карту .HGT", command=self.load_file)
        self.btn_load.pack(pady=10, padx=10, fill="x")

        self.btn_plot = ctk.CTkButton(self.sidebar, text="Построить профиль",
                                      command=self.show_profile_window, fg_color="#2c5d2c")
        self.btn_plot.pack(pady=10, padx=10, fill="x")

        self.btn_clear = ctk.CTkButton(self.sidebar, text="Сбросить точки",
                                       command=self.clear_points, fg_color="#777777")
        self.btn_clear.pack(pady=5, padx=10, fill="x")

        # Карта (справа) - Белый фон контейнера
        self.plot_frame = ctk.CTkFrame(self, fg_color="#FFFFFF")
        self.plot_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Настройка Matplotlib для белой темы
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
        ctk.CTkLabel(master, text=label_text, justify="left", anchor="w", text_color="black").pack(pady=(5, 0), padx=10,
                                                                                                   fill="x")
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
            self.ax.set_facecolor('#F9F9F9')
            # Используем 'gist_earth' или 'terrain' - они хорошо смотрятся на белом
            self.ax.imshow(self.current_matrix, extent=self.map_extent, cmap='terrain', origin='upper')
            self.ax.tick_params(colors='black')
            for p in self.points:
                self.ax.plot(p[1], p[0], 'ro', markersize=7, markeredgecolor='white')
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

        try:
            h1 = float(self.h1_entry.get())
            h2 = float(self.h2_entry.get())
            f_frenel = float(self.f_frenel_entry.get())
            f_max = float(self.f_max_entry.get())
        except ValueError:
            h1, h2, f_frenel = 15, 15, 2.4

        earth_arc = app_logic.get_earth_arc(dist)
        elev_curved = elev + earth_arc
        los_line = np.linspace(elev_curved[0] + h1, elev_curved[-1] + h2, len(dist))
        f_radius = app_logic.get_fresnel_zone(dist, total_dist, f_frenel)

        top = ctk.CTkToplevel(self)
        top.title("Анализ профиля трассы")
        top.geometry("1100x600")
        top.configure(fg_color="#FFFFFF")

        fig_p = Figure(figsize=(8, 5), dpi=100, facecolor='#FFFFFF')
        ax_p = fig_p.add_subplot(111)
        ax_p.set_facecolor('#FCFCFC')
        ax_p.tick_params(colors='black')

        ax_p.fill_between(dist, earth_arc, -100, color='#ADD8E6', alpha=0.3, label='Кривизна Земли')
        ax_p.fill_between(dist, elev_curved, earth_arc, color='#8B4513', alpha=0.6, label='Рельеф')
        ax_p.fill_between(dist, los_line - f_radius, los_line + f_radius, color='#FFA500', alpha=0.2,
                          label=f'Зона Френеля ({f_frenel} ГГц)')
        ax_p.plot(dist, los_line, 'b--', label='Линия LOS', lw=1.5)

        ax_p.set_title(f"Профиль трассы (f = {f_max} МГц)", color='black')
        ax_p.set_xlabel("Дистанция (м)", color='black')
        ax_p.set_ylabel("Высота (м)", color='black')
        ax_p.legend(loc='upper right', frameon=True, facecolor='white')
        ax_p.grid(True, alpha=0.3, color='gray')

        canvas_p = FigureCanvasTkAgg(fig_p, master=top)
        canvas_p.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        canvas_p.get_tk_widget().configure(bg='#FFFFFF', highlightthickness=0)
        canvas_p.draw()