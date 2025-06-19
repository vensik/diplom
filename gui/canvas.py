# gui/canvas.py
import numpy as np
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QCursor, QRegion, QPolygonF
from PyQt5.QtCore import Qt, QTimer, QPointF, QPoint

from ai.classes import CLASSES, PATHOLOGIES, EXTRA, RAW_TO_HUMAN

DISEASE_COLORS = {
    "Periodontit": QColor(255, 60, 60, 180),
    "caries": QColor(255, 120, 60, 180),
    "cyst": QColor(255, 80, 180, 180),
    "radix": QColor(200, 60, 255, 180),
    "supplemental": QColor(230, 180, 60, 180),
    "missing teeth": QColor(255, 80, 80, 180),
    # Приглушённые цвета для следов лечения и extra
    "filling": QColor(60, 180, 255, 80),
    "crown": QColor(130, 190, 255, 80),
    "implant": QColor(60, 120, 220, 70),
    "mini implant": QColor(120, 180, 220, 70),
    "sealed channel": QColor(100, 150, 220, 70),
    "artefact": QColor(150, 150, 150, 40),
    "bracket": QColor(200, 200, 80, 60),
    "eights": QColor(100, 100, 180, 30),
    "retailer": QColor(150, 100, 200, 40),
}

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.image_path = None
        self.segments = []
        self.visible_segments = []
        self.active_labels = set()

        # Для масштабирования и перемещения
        self.scaled_cache = None
        self.scale_factor = 1.0
        self.scale_factor_changed = True 
        self.drag_pos = QPoint() 
        self.image_offset = QPointF(0, 0)


        # Для анимации
        self.analysis_progress = 0
        self.animating = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)

        self.detection_timer = QTimer()
        self.detection_timer.timeout.connect(self.reveal_next_segment)

        self.drag_pos = QPoint()  # Для перемещения изображения
        self.image_offset = QPointF(0, 0)  # Смещение изображения
        self.setMouseTracking(True)  # Включаем отслеживание мыши


    def set_image(self, image_path):
        self.image = QPixmap(image_path)
        self.image_path = image_path
        self.scale_factor = 1.0
        self.scale_factor_changed = True
        self.scaled_cache = None  # Сбрасываем кэш при новой картинке
        self.update()

    def update_animation(self):
        if not self.animating:
            return
        self.analysis_progress += 5
        if self.analysis_progress > self.width():
            self.animating = False
            self.timer.stop()
        self.update()

    def set_segments(self, segments):
        self.segments = segments
        self.visible_segments = segments
        self.active_labels = set(s['label'] for s in segments)
        self.update() 

    def reveal_next_segment(self):
        if len(self.visible_segments) < len(self.segments):
            self.visible_segments.append(self.segments[len(self.visible_segments)])
            self.update()
        else:
            self.detection_timer.stop()

    def set_active_labels(self, labels: set):
        if not labels:
            labels = set(seg['label'] for seg in self.segments)
        self.active_labels = labels
        self.visible_segments = [seg for seg in self.segments if seg['label'] in self.active_labels]
        self.update()

    def zoom_in(self):
        self.scale_factor *= 1.25
        self.scale_factor_changed = True
        self.update()

    def zoom_out(self):
        self.scale_factor *= 0.8
        self.scale_factor_changed = True
        self.update()

    def fit_to_window(self):
        if not self.image:
            return
        widget_size = self.size()
        img_size = self.image.size()
        scale_w = widget_size.width() / img_size.width()
        scale_h = widget_size.height() / img_size.height()
        self.scale_factor = min(scale_w, scale_h)
        self.image_offset = QPointF(0, 0)
        self.scale_factor_changed = True
        self.update()

    def wheelEvent(self, event):
        zoom_factor = 1.2
        if event.angleDelta().y() > 0:
            # Приближение
            self.scale_factor *= zoom_factor
        else:
            # Отдаление
            self.scale_factor /= zoom_factor
        
        # Ограничиваем масштаб
        self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
        self.scale_factor_changed = True
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            delta = event.pos() - self.drag_pos
            self.drag_pos = event.pos()
            self.image_offset += delta
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event):
        if not self.image:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Обновляем кэш при необходимости
        if self.scaled_cache is None or self.scale_factor_changed:
            self.scaled_cache = self.image.scaled(
                int(self.image.width() * self.scale_factor),
                int(self.image.height() * self.scale_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.scale_factor_changed = False

        # Центрирование изображения
        x = int((self.width() - self.scaled_cache.width()) // 2 + self.image_offset.x())
        y = int((self.height() - self.scaled_cache.height()) // 2 + self.image_offset.y())
        painter.drawPixmap(x, y, self.scaled_cache)

        # Затемняем весь снимок
        dark_color = QColor(0, 0, 0, 170)  # 170 из 255 ~70% затемнение
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.fillRect(x, y, self.scaled_cache.width(), self.scaled_cache.height(), dark_color)

        # Ярко выделяем только отмеченные зубы (поверх затемнения)
        img_w, img_h = self.image.width(), self.image.height()
        scale_w = self.scaled_cache.width() / img_w
        scale_h = self.scaled_cache.height() / img_h
        for segment in self.visible_segments:
            if segment['label'] not in self.active_labels:
                continue

            # Только для зубов!
            if segment.get('is_tooth', False) or segment['label'].startswith("tooth"):
                # Создаем QPixmap-маску
                tooth_mask = QPixmap(self.scaled_cache.size())
                tooth_mask.fill(Qt.transparent)
                tooth_painter = QPainter(tooth_mask)
                tooth_painter.setRenderHint(QPainter.Antialiasing)
                path = []
                for px, py in np.array(segment['points']):
                    sx = int(px * scale_w)
                    sy = int(py * scale_h)
                    path.append(QPointF(sx, sy))
                if len(path) > 2:
                    # Маска зуба — белым цветом
                    tooth_painter.setPen(Qt.NoPen)
                    tooth_painter.setBrush(QBrush(Qt.white))
                    tooth_painter.drawPolygon(*path)
                tooth_painter.end()

                # Вырезаем область зуба с оригинального снимка
                tooth_pixmap = QPixmap(self.scaled_cache.size())
                tooth_pixmap.fill(Qt.transparent)
                cut_painter = QPainter(tooth_pixmap)
                cut_painter.setClipRegion(QRegion(QPolygonF(path).toPolygon()))
                cut_painter.drawPixmap(0, 0, self.scaled_cache)
                cut_painter.end()

                # Повышаем яркость (белым Screen-режимом)
                highlight_painter = QPainter(tooth_pixmap)
                highlight_painter.setCompositionMode(QPainter.CompositionMode_Screen)
                highlight_painter.setClipRegion(QRegion(QPolygonF(path).toPolygon()))
                highlight_painter.fillRect(tooth_pixmap.rect(), QColor(255, 255, 255, 70))
                highlight_painter.end()

                # Рисуем выделенный зуб поверх затемнения
                painter.drawPixmap(x, y, tooth_pixmap)

                # Подпись номера зуба
                painter.setPen(Qt.white)
                label_x = sum(p.x() for p in path) / len(path)
                label_y = sum(p.y() for p in path) / len(path)
                pos = segment['label'].split()[-1]
                font = painter.font()
                font.setBold(True)
                font.setPointSize(14)  # Можно изменить размер
                painter.setFont(font)
                painter.drawText(int(label_x) + x, int(label_y) + y, pos)

             # Патологии 
            elif segment.get('is_pathology', False):
                label = segment['label']
                path = [
                    QPointF(x + (px * scale_w), y + (py * scale_h))
                    for px, py in segment['points']
                ]
                if len(path) > 2:
                    color = DISEASE_COLORS.get(label, QColor(255, 0, 0, 160))
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(color))
                    painter.drawPolygon(*path)
                    cx = sum(p.x() for p in path) / len(path)
                    cy = sum(p.y() for p in path) / len(path)
                    painter.setPen(Qt.yellow)
                    painter.drawText(int(cx), int(cy), RAW_TO_HUMAN[label])
                continue

            if segment.get('is_extra', False):
                label = segment['label']
                path = [
                    QPointF(x + (px * scale_w), y + (py * scale_h))
                    for px, py in segment['points']
                ]
                if len(path) > 2:
                    color = DISEASE_COLORS.get(label, QColor(80, 130, 180, 60))
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(color))
                    painter.drawPolygon(*path)
                continue