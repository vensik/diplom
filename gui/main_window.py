# gui/main_window.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit, QListWidget, QCheckBox,
    QVBoxLayout, QHBoxLayout, QFileDialog, QListWidgetItem, QFrame
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt
from gui.canvas import Canvas
from gui.filter_panel import FilterPanel
from ai.diagnosis import diagnose_image, get_row_from_label

class DentalDiagnosisApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OPG Scanner")
        self.setMinimumSize(1000, 700)
        self.init_ui()

    def init_ui(self):
        # Левая панель
        self.load_btn = QPushButton("Загрузить снимок")
        self.save_btn = QPushButton("Сохранить результат")

        self.zoom_in_btn = QPushButton("Увеличить")
        self.zoom_out_btn = QPushButton("Уменьшить")
        self.fit_btn = QPushButton("Выровнять по окну")

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.load_btn)
        left_layout.addWidget(self.save_btn)
        left_layout.addWidget(self.zoom_in_btn)
        left_layout.addWidget(self.zoom_out_btn)
        left_layout.addWidget(self.fit_btn)
        left_layout.addStretch()

        # Зона снимка с отрисовкой
        self.canvas = Canvas()
        self.canvas.setMinimumSize(400, 400)

        # Правая панель
        self.filter_panel = FilterPanel(on_filter_changed=self.on_filter_changed)
        self.recent_label = QLabel("Последние сканирования")
        self.recent_scans = QListWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.filter_panel)
        right_layout.addWidget(self.recent_label)
        right_layout.addWidget(self.recent_scans)

        # Панель последних сканирований
        self.recent_label = QLabel("Последние сканирования")
        self.recent_scans = QListWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(self.filter_panel)
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
        self.load_btn.clicked.connect(self.load_image)
        self.save_btn.clicked.connect(self.save_result)

        self.zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        self.zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        self.fit_btn.clicked.connect(self.canvas.fit_to_window)

    def log(self, text):
        self.log_output.append(text)

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать снимок", "", "Изображения (*.png *.jpg *.jpeg)")
        if path:
            self.canvas.set_image(path)
            self.log(f"Загружен снимок: {path.split('/')[-1]}")
            self.recent_scans.addItem(f"Снимок: {path.split('/')[-1]}")
            self.analyze_image()

    def on_filter_changed(self):
        active_rows = self.filter_panel.get_active_rows()
        active_diseases = self.filter_panel.get_active_diseases()
        visible = []
        for seg in self.canvas.segments:
            if seg['label'].startswith("tooth"):
                if get_row_from_label(seg['label']) in active_rows:
                    visible.append(seg)
            else:
                if seg['label'] in active_diseases:
                    visible.append(seg)

        self.canvas.visible_segments = visible
        self.canvas.active_labels = {seg['label'] for seg in visible}
        self.canvas.update()

    def analyze_image(self):
        if not hasattr(self.canvas, 'image_path'):
            self.log("[Ошибка] Изображение не загружено")
            return
        try:
            self.log("Начало анализа...")
            messages, segments = diagnose_image(self.canvas.image_path)

            for msg in messages:
                self.log(msg)

            self.canvas.set_teeth(segments)
            # self.canvas.set_disease_masks(disease_masks)

            row_names = set(get_row_from_label(seg['label']) for seg in segments if seg['label'].startswith('tooth'))
            # если патологии не визуализируются на снимке, то их можно не выделять
            disease_labels = set(seg['label'] for seg in segments if not seg['label'].startswith('tooth'))
            self.filter_panel.update_rows(row_names)
            self.filter_panel.update_diseases(disease_labels)
            self.on_filter_changed()
        except Exception as e:
            self.log(f"[Ошибка] {str(e)}")
            import traceback
            print(f"Полная ошибка: {traceback.format_exc()}")


    def save_result(self):
        self.log("Результат оохранен")
        # Логика сохранения результата (пока заглушка)