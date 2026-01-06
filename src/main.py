"""
WhisperType - Simplified voice dictation for Windows
Fork of whisper-writer with minimal UI (systray only)
"""
import os
import sys
import subprocess
import pyperclip
from audioplayer import AudioPlayer
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction

from key_listener import KeyListener
from result_thread import ResultThread
from transcription import create_local_model
from input_simulation import InputSimulator
from utils import ConfigManager


class WhisperTypeApp(QObject):
    """
    Minimal voice dictation app with systray-only interface.
    """

    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running with just systray

        # Set icon
        icon_path = os.path.join('assets', 'ww-logo.png')
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))

        # Initialize config
        ConfigManager.initialize()

        # Initialize components
        self.initialize_components()

    def initialize_components(self):
        """Initialize all application components."""
        # Input simulator for typing transcription
        self.input_simulator = InputSimulator()

        # Key listener for hotkey
        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)

        # Load local Whisper model
        model_options = ConfigManager.get_config_section('model_options')
        self.local_model = create_local_model() if not model_options.get('use_api') else None

        self.result_thread = None
        self.is_recording = False

        # Create systray
        self.create_tray_icon()

        # Start listening for hotkey
        self.key_listener.start()

        ConfigManager.console_print('WhisperType ready. Press hotkey to start recording.')

    def create_tray_icon(self):
        """Create the system tray icon and context menu."""
        icon_path = os.path.join('assets', 'ww-logo.png')
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self.app)

        tray_menu = QMenu()

        # Open config action
        config_action = QAction('Open Config', self.app)
        config_action.triggered.connect(self.open_config)
        tray_menu.addAction(config_action)

        tray_menu.addSeparator()

        # Exit action
        exit_action = QAction('Quit', self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip('WhisperType - Ready')
        self.tray_icon.show()

    def open_config(self):
        """Open the config file in default editor."""
        config_path = os.path.join('src', 'config.yaml')
        if sys.platform == 'win32':
            os.startfile(config_path)
        elif sys.platform == 'darwin':
            subprocess.run(['open', config_path])
        else:
            subprocess.run(['xdg-open', config_path])

    def cleanup(self):
        """Clean up resources."""
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()

    def exit_app(self):
        """Exit the application."""
        self.cleanup()
        QApplication.quit()

    def play_start_sound(self):
        """Play sound when recording starts."""
        if ConfigManager.get_config_value('misc', 'noise_on_start'):
            sound_path = os.path.join('assets', 'start.wav')
            if os.path.exists(sound_path):
                AudioPlayer(sound_path).play(block=False)

    def play_end_sound(self):
        """Play sound when recording ends."""
        if ConfigManager.get_config_value('misc', 'noise_on_completion'):
            sound_path = os.path.join('assets', 'beep.wav')
            if os.path.exists(sound_path):
                AudioPlayer(sound_path).play(block=True)

    def on_activation(self):
        """Called when the activation key is pressed."""
        if self.result_thread and self.result_thread.isRunning():
            # Already recording - stop it
            recording_mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
            if recording_mode == 'press_to_toggle':
                self.result_thread.stop_recording()
            elif recording_mode == 'continuous':
                self.stop_result_thread()
            return

        # Start recording
        self.play_start_sound()
        self.is_recording = True
        self.tray_icon.setToolTip('WhisperType - Recording...')
        self.start_result_thread()

    def on_deactivation(self):
        """Called when the activation key is released."""
        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'hold_to_record':
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()

    def start_result_thread(self):
        """Start the recording and transcription thread."""
        if self.result_thread and self.result_thread.isRunning():
            return

        self.result_thread = ResultThread(self.local_model)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.statusSignal.connect(self.on_status_change)
        self.result_thread.start()

    def stop_result_thread(self):
        """Stop the result thread."""
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()

    def on_status_change(self, status):
        """Update tooltip based on status."""
        status_messages = {
            'recording': 'WhisperType - Recording...',
            'transcribing': 'WhisperType - Transcribing...',
            'idle': 'WhisperType - Ready',
            'error': 'WhisperType - Error'
        }
        self.tray_icon.setToolTip(status_messages.get(status, 'WhisperType'))

    def on_transcription_complete(self, result):
        """Handle completed transcription."""
        self.is_recording = False
        self.tray_icon.setToolTip('WhisperType - Ready')

        if result:
            # Copy to clipboard
            if ConfigManager.get_config_value('output', 'copy_to_clipboard'):
                try:
                    pyperclip.copy(result)
                    ConfigManager.console_print(f'Copied to clipboard: {result}')
                except Exception as e:
                    ConfigManager.console_print(f'Clipboard error: {e}')

            # Type the result (if enabled)
            if ConfigManager.get_config_value('output', 'auto_type'):
                self.input_simulator.typewrite(result)

        # Play completion sound
        self.play_end_sound()

        # Handle continuous mode
        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'continuous':
            self.start_result_thread()
        else:
            self.key_listener.start()

    def run(self):
        """Start the application."""
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    app = WhisperTypeApp()
    app.run()
