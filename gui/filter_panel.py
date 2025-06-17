# gui/filter_panel.py

from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QLabel, QPushButton, QCheckBox

class FilterPanel(QWidget):
    def __init__(self, on_filter_changed=None, parent=None):
        super().__init__(parent)
        self.on_filter_changed = on_filter_changed
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        # ---- Панель для рядов ----
        self.layout.addWidget(QLabel("Ряды зубов"))
        self.row_grid = QGridLayout()
        self.layout.addLayout(self.row_grid)
        self.row_buttons = {}

        # Кнопка "Скрыть все" для рядов
        hide_btn = QPushButton("Скрыть все")
        hide_btn.clicked.connect(self.hide_all_rows)
        self.layout.addWidget(hide_btn)
        self.hide_btn = hide_btn

        # ---- Панель для патологий ----
        self.layout.addWidget(QLabel("Патологии"))
        self.disease_layout = QVBoxLayout()
        self.layout.addLayout(self.disease_layout)
        self.disease_checkboxes = {}

    def update_rows(self, row_names):
        # Удалить старые кнопки
        for i in reversed(range(self.row_grid.count())):
            widget = self.row_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.row_buttons.clear()
        
        positions = [(0,0),(0,1),(1,0),(1,1)]
        for idx, row in enumerate(sorted(row_names)):
            btn = QPushButton(row)
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.clicked.connect(self._trigger_callback)
            btn.setProperty("rowButton", True)
            pos = positions[idx] if idx < 4 else (2, 0, 1, 2)
            self.row_buttons[row] = btn
            if len(pos) == 2:
                self.row_grid.addWidget(btn, *pos)
            else:
                self.row_grid.addWidget(btn, *pos)

    def update_diseases(self, disease_labels):
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
        return [name for name, btn in self.row_buttons.items() if btn.isChecked()]

    def get_active_diseases(self):
        return [name for name, cb in self.disease_checkboxes.items() if cb.isChecked()]

    def hide_all_rows(self):
        for btn in self.row_buttons.values():
            btn.setChecked(False)
        self._trigger_callback()

    def _trigger_callback(self):
        if self.on_filter_changed:
            self.on_filter_changed()
