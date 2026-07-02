'''
Sift UI: media controls
'''

# -- Import external dependencies --
from PySide6.QtCore import Qt, Signal
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
)

# -- SEEK_BASE_MS & VOLUME_STEP: variables for defining single steps --
SEEK_BASE_MS = 5000
VOLUME_STEP = 0.05

# -- _format_ms: converts milliseconds to seconds -- 
def _format_ms(ms: int) -> str:
    s = max(0, ms) // 1000
    return f'{s // 60:02d}:{s % 60:02d}'

# -- ScrubSlider: class defining a horizontal slider reporting value under the cursor (on hover) --
class ScrubSlider(QSlider):
    hovered = Signal(int)
    
    # Initialise QSlider
    def __init__(self) -> None:
        super().__init__(Qt.Orientation.Horizontal)
        self.setMouseTracking(True)
    
    # _value_at: get current value
    def _value_at(self, x: int) -> int:
        return QStyle.sliderValueFromPosition(
            self.minimum(), self.maximum(), x, self.width()
        )
    
    # mouseMoveEvent: on hover, calculate and emit value
    def mouseMoveEvent(self, event):
        self.hovered.emit(self._value_at(int(event.position().x())))
        super().mouseMoveEvent(event)


# -- SpeakerButton: class defining a speaker glyph which reflects current volume level --
class SpeakerButton(QLabel):
    toggled_mute = Signal()
    
    # Initialise button
    def __init__(self) -> None:
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(24)
        self.set_level(0.8, muted=False)

    # set_level: set icon based on volume level
    def set_level(self, volume: float, muted: bool) -> None:
        if muted or volume <= 0:
            glyph = '\U0001F507'   # muted speaker
        elif volume < 0.34:
            glyph = '\U0001F508'   # low volume
        elif volume < 0.67:
            glyph = '\U0001F509'   # medium volume
        else:
            glyph = '\U0001F50A'   # high volume
        self.setText(glyph)
    
    # mousePressEvent: on mouse press, toggle mute
    def mousePressEvent(self, _event) -> None:
        self.toggled_mute.emit()


# -- MediaControls: class define structure of media controls panel (play/pause, seek slider, time, volume)
class MediaControls(QWidget):
    # Initialise QWidget
    def __init__(self, player: QMediaPlayer, audio_output) -> None: 
        super().__init__()
        self.player = player
        self.audio = audio_output
        self._volume = 0.8
        self._muted = False
        self.audio.setVolume(self._volume)
        # Set up media controls layout
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        # Add play/pause button
        self.play_btn = QPushButton('Pause')
        self.play_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.play_btn.clicked.connect(self.toggle)
        # Add scrub slider
        self.position = ScrubSlider()
        self.position.hovered.connect(self._scrub_to)
        self.position.sliderMoved.connect(self.player.setPosition)
        # Add time label
        self.time_label = QLabel('00:00 / 00:00')
        # Add speaker button
        self.speaker = SpeakerButton()
        self.speaker.toggled_mute.connect(self.toggle_mute)
        # Add volume slider
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(int(self._volume * 100))
        self.volume.setFixedWidth(110)
        self.volume.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.volume.valueChanged.connect(self._on_volume_slider)
        # Add media controls to layout
        row.addWidget(self.play_btn)
        row.addWidget(self.position, stretch=1)
        row.addWidget(self.time_label)
        row.addWidget(self.speaker)
        row.addWidget(self.volume)
        layout.addLayout(row)
        # Connect helpers to state changes
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)

    # toggle: toggles the playback state to pause or play depending on if media is playing
    def toggle(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    # seek_relative: changes media player position to be the current plus a given number of milliseconds
    def seek_relative(self, ms: int) -> None:
        pos = self.player.position() + ms
        self.player.setPosition(max(0, min(pos, self.player.duration())))
    
    # _scrub_to: sets the media player position to the provided value
    def _scrub_to(self, value: int) -> None:
        self.player.setPosition(value)

    # change_volume: changes the volume by a given value
    def change_volume(self, delta: float) -> None:
        self._muted = False
        self._volume = max(0.0, min(1.0, self._volume + delta))
        self.volume.setValue(int(self._volume * 100))

    # toggle_mute: toggles between muted/unmuted media
    def toggle_mute(self) -> None:
        self._muted = not self._muted
        self.audio.setVolume(0.0 if self._muted else self._volume)
        self.speaker.set_level(self._volume, self._muted)

    # _on_volume_slider: sets the volume level to the selected value from the volume slider
    def _on_volume_slider(self, v: int) -> None:
        self._volume = v / 100
        self._muted = False
        self.audio.setVolume(self._volume)
        self.speaker.set_level(self._volume, self._muted)


    # _on_position: sets the current time
    def _on_position(self, pos: int) -> None:
        if not self.position.isSliderDown():
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