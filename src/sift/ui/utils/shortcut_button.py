'''
Sift UI: shortcut button component
'''

# -- Import external dependencies --
from PySide6.QtGui import QStandardItem
from PySide6.QtWidgets import (
    QPushButton,
    QStyle,
    QStyleOptionButton,
    QStylePainter,
)

# -- ShortcutButton: class defining a custom button with an underlined shortcut key --
class ShortcutButton(QPushButton):
    def __init__(self, text: str, underline_index: int = -1) -> None:
        super().__init__(text)
        self.underline_index = underline_index

    def paintEvent(self, _event) -> None:
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        opt.text = ''
        painter = QStylePainter(self)
        painter.drawControl(QStyle.ControlElement.CE_PushButton, opt)
        text = self.text()
        fm = self.fontMetrics()
        rect = self.rect()
        tw = fm.horizontalAdvance(text)
        x = (rect.width() - tw) // 2
        y = (rect.height() + fm.ascent() - fm.descent()) // 2
        painter.drawText(x, y, text)
        if 0 <= self.underline_index < len(text):
            pre = fm.horizontalAdvance(text[: self.underline_index])
            cw = fm.horizontalAdvance(text[self.underline_index])
            uy = y + 2
            painter.drawLine(x + pre, uy, x + pre + cw, uy)
        painter.end()