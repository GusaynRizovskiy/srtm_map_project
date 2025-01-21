import sys
import numpy as np
import rasterio
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPalette, QBrush, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from form_of_window import Form1


#Основной класс программы
class Form_main(QtWidgets.QMainWindow,Form1):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    form = Form_main()
    palette = QPalette()
    palette.setBrush(QPalette.Background, QBrush(QPixmap("picture.webp")))
    form.setPalette(palette)
    form.show()
    sys.exit(app.exec_())