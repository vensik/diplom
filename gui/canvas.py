# gui/canvas.py

from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QCursor
from PyQt5.QtCore import Qt, QTimer, QPointF, QPoint
from ai.diagnosis import get_row_from_label

ROW_COLORS = {
    "верхний правый": QColor(70, 70, 70, 120),
    "верхний левый": QColor(130, 130, 130, 120),
    "нижний левый": QColor(180, 180, 180, 120),
    "нижний правый": QColor(220, 220, 220, 120),
    "не определён": QColor(190, 190, 190, 120)
}

DISEASE_COLORS = {
    "caries": QColor(255, 0, 0, 150),
    "periapical pathology": QColor(0, 255, 0, 150),
    "calculus": QColor(255, 165, 0, 150),
    "implant": QColor(128, 0, 128, 150),
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


        # Для анимации (если нужно)
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

    def set_teeth(self, teeth):
        self.segments = teeth
        self.visible_segments = teeth.copy()
        self.active_labels = {seg['label'] for seg in teeth}
        self.update()
    
    def set_disease_masks(self, disease_masks):
        self.disease_masks = {name: data['mask'] for name, data in disease_masks.items()}
        self.update()

    def reveal_next_segment(self):
        if len(self.visible_segments) < len(self.segments):
            self.visible_segments.append(self.segments[len(self.visible_segments)])
            self.update()
        else:
            self.detection_timer.stop()

    def set_active_labels(self, labels: set):
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

        # Сначала — зубы (серые по ряду)
        for segment in self.visible_segments:
            if segment['label'] not in self.active_labels:
                continue

            if segment['label'].startswith("tooth"):
                row = get_row_from_label(segment['label'])
                color = ROW_COLORS.get(row, ROW_COLORS["не определён"])
            else:
                # Патология — цветной слой
                color = DISEASE_COLORS.get(segment['label'].lower(), QColor(0, 0, 255, 150))

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)

            # Преобразование координат
            path = []
            img_w, img_h = self.image.width(), self.image.height()
            scale_w = self.scaled_cache.width() / img_w
            scale_h = self.scaled_cache.height() / img_h
            
            for px, py in segment['points']:
                sx = x + (px * scale_w)
                sy = y + (py * scale_h)
                path.append(QPointF(sx, sy))

            # Рисуем полигон
            if len(path) > 2:
                painter.drawPolygon(*path)
                # Подпись только для зубов
                if segment['label'].startswith("tooth"):
                    painter.setPen(Qt.white)
                    label_x = min(p.x() for p in path)
                    label_y = min(p.y() for p in path)
                    # Только номер в ряду!
                    pos = segment['label'].split()[-1][-1]
                    painter.drawText(int(label_x), int(label_y) - 5, pos)
                else:
                    # Для патологий — подпись названия болезни
                    painter.setPen(Qt.yellow)
                    label_x = min(p.x() for p in path)
                    label_y = max(p.y() for p in path)
                    painter.drawText(int(label_x), int(label_y) + 15, segment['label'])
