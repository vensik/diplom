from PyQt5.QtWidgets import (
    QMainWindow, QLabel, QPushButton, 
    QFileDialog, QVBoxLayout, QWidget, 
    QHBoxLayout, QCheckBox, QGroupBox
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt
from ai.diagnostician import predict_image
from gui.detection_canvas import DetectionCanvas
from gui.detection_canvas import Segment
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Диагностика зубов")
        self.setGeometry(300, 100, 1200, 800)

        # Главное содержимое
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной горизонтальный макет
        self.main_layout = QHBoxLayout()
        central_widget.setLayout(self.main_layout)

        # Левая часть (управление + изображение + кнопка)
        left_panel = QVBoxLayout()

        # Область изображения
        self.canvas = DetectionCanvas()
        left_panel.addWidget(self.canvas, stretch=1)

        # Кнопка загрузки изображения
        self.upload_button = QPushButton("Загрузить рентген-снимок")
        self.upload_button.clicked.connect(self.load_image)
        left_panel.addWidget(self.upload_button, alignment=Qt.AlignCenter)

        # Результат диагностики
        self.result_label = QLabel("")
        self.result_label.setObjectName("resultLabel")
        self.result_label.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(self.result_label)

        self.main_layout.addLayout(left_panel, stretch=3)

        # Правая часть (фильтрация сегментов)
        self.filter_group = QGroupBox("Переключение отображения сегментов")
        self.filter_layout = QVBoxLayout()
        self.filter_group.setLayout(self.filter_layout)
        self.main_layout.addWidget(self.filter_group, stretch=1)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать изображение", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            # Отображаем картинку
            self.canvas.set_image(file_path)

            # Диагностика
            label, confidence = predict_image(file_path)
            self.result_label.setText(
                f"<b>Результат:</b> {label} ({confidence * 100:.1f}%)"
            )

            # Заглушка сегментации
            segments = [
                Segment(
                    points=[(100, 120), (130, 110), (150, 140), (120, 160)],
                    label="Кариес"
                ),
                Segment(
                    points=[(220, 240), (260, 230), (270, 270), (230, 280)],
                    label="Пульпит"
                )
            ]
            self.canvas.set_segments(segments)
            self.update_filter_checkboxes()

    
    def update_filter_checkboxes(self):
        for i in reversed(range(self.filter_layout.count())):
            widget = self.filter_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        labels = sorted(set(seg.label for seg in self.canvas.segments))
        self.checkboxes = {}

        for label in labels:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.stateChanged.connect(self.on_filter_changed)
            self.filter_layout.addWidget(cb)
            self.checkboxes[label] = cb

    def on_filter_changed(self):
        active = {label for label, cb in self.checkboxes.items() if cb.isChecked()}
        self.canvas.set_active_labels(active)


