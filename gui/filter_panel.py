# gui/filter_panel.py
import os
from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QPushButton, QCheckBox, QSizePolicy, QStyle, QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

class FilterPanel(QWidget):
    def __init__(self, on_filter_changed=None, parent=None):
        super().__init__(parent)
        self.on_filter_changed = on_filter_changed
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # ---- Панель для зубов ----
        self.layout.addWidget(QLabel("Ряды зубов"))
        self.top_row_layout = QHBoxLayout()
        self.top_row_layout.setSpacing(8)
        self.layout.addLayout(self.top_row_layout) 

        # Сетка для рядов
        self.row_grid = QGridLayout()
        self.layout.addLayout(self.row_grid)
        self.row_buttons = {}

        # ---- Панель для патологий ----
        self.layout.addWidget(QLabel("Патологии"))
        self.disease_layout = QVBoxLayout()
        self.layout.addLayout(self.disease_layout)
        self.disease_checkboxes = {}

    ICON_EYE = os.path.join(os.path.dirname(__file__), "icons/eye-regular.svg")
    ICON_EYE_SLASH = os.path.join(os.path.dirname(__file__), "icons/eye-regular-slash.svg")

    def update_rows(self, row_names):
        while self.top_row_layout.count():
            item = self.top_row_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # Кнопка скрыть
        self.hide_btn = QPushButton()
        self.hide_btn.setCheckable(True)
        self.hide_btn.setFixedSize(32, 32)
        self.hide_btn.setIcon(QIcon(self.ICON_EYE))
        self.hide_btn.setIconSize(QSize(24, 24))
        self.hide_btn.clicked.connect(self.toggle_hide)
        self.top_row_layout.addWidget(self.hide_btn)

        self.buds_btn = QPushButton("Зачатки")
        self.buds_btn.setCheckable(True)
        self.buds_btn.setChecked(True)
        self.buds_btn.setMaximumHeight(32)
        self.buds_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.buds_btn.clicked.connect(self.toggle_buds)
        self.top_row_layout.addWidget(self.buds_btn)

        for i in reversed(range(self.row_grid.count())):
            widget = self.row_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.row_buttons.clear()

        def is_bud_row(r):
            val = str(r).strip().lower()
            return ("зачат" in val) or ("bud" in val) or (val == "зачатки")
        rows = [r for r in row_names if not is_bud_row(r)]

        # Кнопки рядов 
        for idx, row in enumerate(rows):
            btn = QPushButton(str(row))
            btn.setProperty("rowButton", True)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedSize(80, 60)
            btn.clicked.connect(lambda _, r=row: self.toggle_row(r))
            r_idx = idx // 2
            c_idx = idx % 2 
            self.row_grid.addWidget(btn, r_idx, c_idx)
            self.row_buttons[row] = btn

    def update_diseases(self, disease_labels):
        print("UPDATE_DISEASES called with:", disease_labels)
        for i in reversed(range(self.disease_layout.count())):
            widget = self.disease_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.disease_checkboxes.clear()
        for disease in sorted(disease_labels):
            cb = QCheckBox(disease)
            cb.setChecked(True)
            cb.stateChanged.connect(self._trigger_callback)
            cb.setProperty("diseaseBox", True)
            self.disease_layout.addWidget(cb)
            self.disease_checkboxes[disease] = cb

    def get_active_rows(self):
        rows = [name for name, btn in self.row_buttons.items() if btn.isChecked()]
        if self.buds_btn.isChecked():
            rows.append("Зачатки")
        return rows

    def get_active_diseases(self):
        return [name for name, cb in self.disease_checkboxes.items() if cb.isChecked()]

    def set_row_icon(self, btn, visible):
        style = self.style()
        icon = style.standardIcon(QStyle.ICON_EYE) if visible else style.standardIcon(QStyle.ICON_EYE_SLASH)
        btn.setIcon(icon)

    def toggle_row(self, row):
        self._trigger_callback()

    def toggle_buds(self):
        self._trigger_callback()

    def toggle_hide(self):
        hidden = self.hide_btn.isChecked()
        for btn in self.row_buttons.values():
            btn.setChecked(not hidden)
        self._trigger_callback()

    def _trigger_callback(self):
        if self.on_filter_changed:
            self.on_filter_changed()
