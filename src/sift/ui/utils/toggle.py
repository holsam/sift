'''
Sift UI: toggle switch for replacing checkboxes
'''

# -- Import external dependencies --
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QCheckBox

# -- ToggleSwitch: class defining the toggle switch UI component --
class ToggleSwitch(QCheckBox):
    # Initialise class
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # sizeHint: sets the toggle's size
    def sizeHint(self) -> QSize:
        return QSize(48, 26)

    # hitButton: returns True when selected
    def hitButton(self, _pos) -> bool:
        return True

    # paintEvent: paints the toggle switch itself
    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        radius = h / 2
        on = self.isChecked()
        track = QColor("#4caf50") if on else QColor("#bbbbbb")
        p.setBrush(track)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)
        knob = h - 6
        x = w - knob - 3 if on else 3
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QRectF(x, 3, knob, knob))
        p.end()