# gui/detection_canvas.py

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush
from PyQt5.QtCore import Qt, QTimer, QPointF
from collections import namedtuple

# Segment = {'points': [...], 'label': 'кариеc'}
Segment = namedtuple('Segment', ['points', 'label'])




class DetectionCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None  # QPixmap
        self.analysis_progress = 0  # для анимации анализа
        self.animating = False

        # Таймер для запуска анимации анализа
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)

        self.segments = []         # Все сегменты
        self.visible_segments = [] # Для поэтапного показа
        self.detection_timer = QTimer()
        self.detection_timer.timeout.connect(self.reveal_next_segment)

        self.active_labels = set()  # какие метки сейчас разрешены к показу


    def set_image(self, image_path):
        self.image = QPixmap(image_path)
        self.analysis_progress = 0
        self.animating = True
        self.timer.start(30)  # обновление каждые 30 мс
        self.update()

    def update_animation(self):
        if not self.animating:
            return
        self.analysis_progress += 5  # скорость перелива
        if self.analysis_progress > self.width():
            self.animating = False
            self.timer.stop()
        self.update()

    def set_segments(self, segments: list[Segment]):
        self.segments = segments
        self.visible_segments = []
        self.detection_timer.start(300)
        self.active_labels = set(seg.label for seg in segments)  # по умолчанию все включены
    
    def reveal_next_segment(self):
        if len(self.visible_segments) < len(self.segments):
            self.visible_segments.append(self.segments[len(self.visible_segments)])
            self.update()
        else:
            self.detection_timer.stop()

    def set_active_labels(self, labels: set):
        self.active_labels = labels
        # Обновляем видимые сегменты с учётом фильтра
        self.visible_segments = [seg for seg in self.segments if seg.label in self.active_labels]
        self.update()

    def paintEvent(self, event):
        if not self.image:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        scaled = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

        if self.animating:
            # Затемнение
            painter.setBrush(QBrush(QColor(0, 0, 0, 120)))
            painter.drawRect(x, y, scaled.width(), scaled.height())

            # Переливная "волна анализа"
            wave_width = 100
            left = x + self.analysis_progress - wave_width
            painter.setBrush(QBrush(QColor(0, 200, 255, 100)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(left, y, wave_width, scaled.height())

        # Фильтруем сегменты по активным меткам
        if not hasattr(self, 'active_labels'):
            self.active_labels = set(seg.label for seg in self.visible_segments)
        filtered_segments = [seg for seg in self.visible_segments if seg.label in self.active_labels]

        # Отрисовка сегментов (масок)
        for segment in filtered_segments:
            # Цвет сегмента по типу
            if segment.label == "Кариес":
                color = QColor(255, 0, 0, 100)
            elif segment.label == "Пульпит":
                color = QColor(0, 255, 0, 100)
            else:
                color = QColor(0, 0, 255, 100)  # Цвет по умолчанию

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)

            # Масштабируем точки сегмента
            path = []
            for px, py in segment.points:
                sx = x + (px * scaled.width() / self.image.width())
                sy = y + (py * scaled.height() / self.image.height())
                path.append(QPointF(sx, sy))

            # Рисуем полигон, если достаточно точек
            if len(path) > 2:
                painter.drawPolygon(*path)



    



