import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QListWidget, QCheckBox,
    QVBoxLayout, QHBoxLayout, QFileDialog, QListWidgetItem, QFrame
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt
from ai.yolo_segmentation import predict_image
from gui.detection_canvas import DetectionCanvas
from gui.detection_canvas import Segment
from gui.segments_loader import load_segments


class DentalDiagnosisApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("X-ray Scanner")
        self.setMinimumSize(1000, 700)
        self.segments = load_segments()
        self.init_ui()

    def init_ui(self):
        # Левая панель
        self.load_button = QPushButton("Загрузить снимок")
        self.analyze_button = QPushButton("Анализировать")
        self.save_button = QPushButton("Сохранить результат")

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.load_button)
        left_layout.addWidget(self.analyze_button)
        left_layout.addWidget(self.save_button)
        left_layout.addStretch()

        # Зона снимка с отрисовкой
        self.canvas = DetectionCanvas()
        self.canvas.setMinimumSize(400, 400)

        # Правая панель
        self.filter_layout = QVBoxLayout()
        self.filter_layout.addWidget(QLabel("Сегменты"))

        self.checkboxes = {}
        # Создаём чекбоксы динамически на основе меток
        labels = sorted(set(seg.label for seg in self.segments))
        for label in labels:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.stateChanged.connect(self.on_filter_changed)
            self.filter_layout.addWidget(cb)
            self.checkboxes[label] = cb

        self.filter_layout.addStretch()

        # Панель последних сканирований
        self.recent_label = QLabel("Последние сканирования")
        self.recent_scans = QListWidget()
        self.recent_scans.addItem("Снимок №12345")
        self.recent_scans.addItem("Снимок №12344")

        right_layout = QVBoxLayout()
        right_layout.addLayout(self.filter_layout)
        right_layout.addWidget(self.recent_label)
        right_layout.addWidget(self.recent_scans)

        # Нижняя панель отчета
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(120)

        # Основной макет
        top_layout = QHBoxLayout()
        top_layout.addLayout(left_layout)
        top_layout.addWidget(self.canvas, stretch=2)
        top_layout.addLayout(right_layout)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.log_output)

        self.setLayout(main_layout)

        # Связываем кнопки с методами
        self.load_button.clicked.connect(self.load_image)
        self.analyze_button.clicked.connect(self.analyze_image)
        self.save_button.clicked.connect(self.save_result)

    def log(self, text):
        self.log_output.append(text)

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать снимок", "", "Изображения (*.png *.jpg *.jpeg)")
        if path:
            self.canvas.set_image(path)
            self.log(f"Загружен снимок: {path.split('/')[-1]}")
            self.recent_scans.addItem(f"Снимок: {path.split('/')[-1]}")

            self.canvas.set_segments(self.segments)
            self.update_filter_checkboxes()

    def update_filter_checkboxes(self):
        # Обновляем чекбоксы в соответствии с активными сегментами
        labels = sorted(set(seg.label for seg in self.canvas.segments))
        # Удаляем старые чекбоксы
        for i in reversed(range(self.filter_layout.count())):
            widget = self.filter_layout.itemAt(i).widget()
            if widget and isinstance(widget, QCheckBox):
                widget.deleteLater()
        self.checkboxes.clear()

        for label in labels:
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.stateChanged.connect(self.on_filter_changed)
            self.filter_layout.insertWidget(1, cb)  # после заголовка
            self.checkboxes[label] = cb

    def on_filter_changed(self):
        active = {label for label, cb in self.checkboxes.items() if cb.isChecked()}
        self.canvas.set_active_labels(active)

    def analyze_image(self):
        # Заглушка ИИ-анализа
        self.log("[AI] Обнаружено: Кариес (3 участка), Периодонтит (1 участок)")

    def save_result(self):
        self.log("[USER] Нажата кнопка 'Сохранить результат'")
        # Логика сохранения результата (пока заглушка)



