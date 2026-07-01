'''
Sift UI: media controls
'''

# -- Import external dependencies --
from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# -- _format_ms: converts milliseconds to seconds -- 
def _format_ms(ms: int) -> str:
    s = ms // 1000
    return f"{s // 60:02d}:{s % 60:02d}"

# -- MediaControls: class define structure of media controls panel (play/pause, seek slider, time, volume)
class MediaControls(QWidget):
    # Initialise QWidget
    def __init__(self, player: QMediaPlayer, audio_output) -> None: 
        super().__init__()
        self.player = player
        self.audio = audio_output
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.play_btn = QPushButton('Play')
        self.play_btn.clicked.connect(self.toggle)
        self.position = QSlider(Qt.Orientation.Horizontal)
        self.position.sliderMoved.connect(self.player.setPosition)
        self.time_label = QLabel('00:00 / 00:00')
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(80)
        self.volume.setFixedWidth(110)
        self.volume.valueChanged.connect(
            lambda v: self.audio.setVolume(v / 100)
        )
        self.audio.setVolume(0.8)
        row.addWidget(self.play_btn)
        row.addWidget(self.position, stretch=1)
        row.addWidget(self.time_label)
        row.addWidget(QLabel('Volume'))
        row.addWidget(self.volume)
        layout.addLayout(row)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)

    # toggle: toggles the playback state to pause or play depending on if media is playing
    def toggle(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    # _on_position: sets the current time
    def _on_position(self, pos: int) -> None:
        self.position.setValue(pos)
        self.time_label.setText(
            f"{_format_ms(pos)} / {_format_ms(self.player.duration())}"
        )

    # _on_duration: sets the duration of the media
    def _on_duration(self, dur: int) -> None:
        self.position.setRange(0, dur)

    # _on_state: sets the current state of the media (playing/paused)
    def _on_state(self, state) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        self.play_btn.setText('Pause' if playing else 'Play')