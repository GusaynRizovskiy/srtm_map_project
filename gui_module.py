import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter.filedialog as fd
import numpy as np
import app_logic

# Настройки темы
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class RadioApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Радиосвязь: Анализ трассы")
        self.geometry("1300x850")

        # Состояние приложения
        self.hgt_path = None
        self.points = []  # Список кортежей (lat, lon)
        self.map_extent = None  # Границы координат для imshow
        self.current_matrix = None  # Матрица высот в памяти

        self._setup_ui()

    def _setup_ui(self):
        # Настройка сетки окна
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Левая панель управления ---
        self.sidebar = ctk.CTkFrame(self, width=280)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(self.sidebar, text="Параметры", font=("Arial", 20, "bold")).pack(pady=20)

        self.btn_load = ctk.CTkButton(self.sidebar, text="1. Выбрать карту (.hgt)",
                                      command=self.load_file)
        self.btn_load.pack(pady=10, padx=20)

        # Поля ввода
        self.h1_entry = self.create_input(self.sidebar, "Высота антенны 1 (м):", "15")
        self.h2_entry = self.create_input(self.sidebar, "Высота антенны 2 (м):", "15")
        self.freq_entry = self.create_input(self.sidebar, "Частота (ГГц):", "2.4")

        self.btn_plot = ctk.CTkButton(self.sidebar, text="2. Построить профиль",
                                      command=self.show_profile_window, fg_color="#2c5d2c")
        self.btn_plot.pack(pady=20, padx=20)

        self.btn_clear = ctk.CTkButton(self.sidebar, text="Очистить точки",
                                       command=self.clear_points, fg_color="#555555")
        self.btn_clear.pack(pady=10, padx=20)

        # --- Правая панель с картой ---
        self.plot_frame = ctk.CTkFrame(self)
        self.plot_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor='#2b2b2b')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')
        self.ax.tick_params(colors='white')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Регистрация события клика
        self.canvas.mpl_connect('button_press_event', self.on_map_click)

    def create_input(self, master, text, default):
        ctk.CTkLabel(master, text=text).pack(pady=(10, 0))
        entry = ctk.CTkEntry(master)
        entry.insert(0, default)
        entry.pack(pady=(0, 5), padx=20)
        return entry

    def load_file(self):
        """Выбор файла через диалоговое окно и загрузка в память."""
        path = fd.askopenfilename(filetypes=[("HGT files", "*.hgt")])
        if path:
            self.hgt_path = path
            # Загружаем матрицу в память через логический модуль
            self.current_matrix, self.map_extent = app_logic.load_hgt_matrix(path)
            self.points = []  # Сброс точек при смене карты
            self.refresh_map()
            self.btn_load.configure(text="Карта загружена", fg_color="#1f538d")

    def refresh_map(self):
        """Отрисовка карты из памяти БЕЗ вызова диалога файла."""
        if self.current_matrix is not None:
            self.ax.clear()
            # Отображаем рельеф
            self.ax.imshow(self.current_matrix, extent=self.map_extent, cmap='terrain', origin='upper')
            self.ax.set_title(f"Рельеф: {self.hgt_path.split('/')[-1]}", color="white")
            self.ax.tick_params(colors='white')

            # Если точки уже были поставлены (например, после частичной очистки), рисуем их
            for p in self.points:
                self.ax.plot(p[1], p[0], 'ro', markersize=7)
            if len(self.points) == 2:
                lats, lons = zip(*self.points)
                self.ax.plot(lons, lats, 'r--', linewidth=2)

            self.canvas.draw()

    def on_map_click(self, event):
        """Обработка выбора точек на карте."""
        if event.inaxes and self.current_matrix is not None:
            if len(self.points) < 2:
                # Сохраняем (lat, lon)
                self.points.append((event.ydata, event.xdata))
                self.ax.plot(event.xdata, event.ydata, 'ro', markersize=7)

                if len(self.points) == 2:
                    lats, lons = zip(*self.points)
                    self.ax.plot(lons, lats, 'r--', linewidth=2)

                self.canvas.draw()

    def clear_points(self):
        """Удаляет только точки, не запрашивая файл."""
        self.points = []
        self.refresh_map()

    def show_profile_window(self):
        """Создает отдельное окно с графиком профиля."""
        if len(self.points) < 2 or self.hgt_path is None:
            return

        # Расчет данных через app_logic
        dist, elev = app_logic.get_elevation_profile(self.hgt_path, self.points[0], self.points[1])

        # Окно профиля
        top = ctk.CTkToplevel(self)
        top.title("Профиль высот и прямая видимость")
        top.geometry("900x500")
        top.after(100, lambda: top.focus_force())

        fig_p = Figure(figsize=(7, 4), dpi=100)
        ax_p = fig_p.add_subplot(111)

        try:
            h1 = float(self.h1_entry.get())
            h2 = float(self.h2_entry.get())
        except ValueError:
            h1, h2 = 0, 0

        # Построение линии видимости (упрощенно)
        los = np.linspace(elev[0] + h1, elev[-1] + h2, len(dist))

        ax_p.fill_between(dist, elev, color='sienna', alpha=0.3, label='Рельеф')
        ax_p.plot(dist, elev, color='saddlebrown', lw=1.5)
        ax_p.plot(dist, los, 'b--', label='Линия связи')

        ax_p.set_title("Разрез местности")
        ax_p.set_xlabel("Дистанция (м)")
        ax_p.set_ylabel("Высота над уровнем моря (м)")
        ax_p.legend()
        ax_p.grid(True, linestyle=':', alpha=0.6)

        canvas_p = FigureCanvasTkAgg(fig_p, master=top)
        canvas_p.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        canvas_p.draw()