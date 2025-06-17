# main.py

from PyQt5.QtWidgets import QApplication
from gui.main_window import DentalDiagnosisApp
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("gui/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    window = DentalDiagnosisApp()
    window.show()
    
    sys.exit(app.exec_())