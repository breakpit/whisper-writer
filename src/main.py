import os
import sys
import time
from audioplayer import AudioPlayer
from pynput.keyboard import Controller, Listener as KeyboardListener, Key
from PyQt5.QtCore import QObject, QProcess
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox

from key_listener import KeyListener
from result_thread import ResultThread
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from ui.status_window import StatusWindow
from transcription import create_local_model
from input_simulation import InputSimulator
from utils import ConfigManager


def manage_windows_startup(enable):
    """Add or remove WhisperWriter from Windows startup."""
    import shutil
    startup_folder = os.path.join(
        os.environ.get('APPDATA', ''),
        'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
    )
    vbs_source = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'WhisperWriter.vbs')
    vbs_dest = os.path.join(startup_folder, 'WhisperWriter.vbs')

    if enable:
        if os.path.exists(vbs_source):
            shutil.copy(vbs_source, vbs_dest)
            print(f"Added to Windows startup: {vbs_dest}")
    else:
        if os.path.exists(vbs_dest):
            os.remove(vbs_dest)
            print(f"Removed from Windows startup: {vbs_dest}")


class WhisperWriterApp(QObject):
    def __init__(self, preloaded_model=None):
        """
        Initialize the application, opening settings window if no configuration file is found.
        """
        super().__init__()
        self.local_model = preloaded_model  # Store preloaded model before Qt init
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Don't quit when windows are closed
        self.app.setWindowIcon(QIcon(os.path.join('assets', 'ww-logo.png')))

        ConfigManager.initialize()

        self.settings_window = SettingsWindow()
        self.settings_window.settings_closed.connect(self.on_settings_closed)
        self.settings_window.settings_saved.connect(self.restart_app)

        if ConfigManager.config_file_exists():
            self.initialize_components()
        else:
            print('No valid configuration file found. Opening settings window...')
            self.settings_window.show()

    def initialize_components(self):
        """
        Initialize the components of the application.
        """
        self.input_simulator = InputSimulator()

        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)

        # Use preloaded model if available (loaded before PyQt5 to avoid DLL conflict)
        if not hasattr(self, 'local_model') or self.local_model is None:
            model_options = ConfigManager.get_config_section('model_options')
            self.local_model = create_local_model() if not model_options.get('use_api') else None

        self.result_thread = None
        self._last_transcription_time = 0  # Cooldown tracking
        self._processing_transcription = False  # Flag to block activations during processing
        self._any_key_listener = None  # Listener to stop recording on any key press

        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.key_listener.start)
        self.main_window.closeApp.connect(self.exit_app)

        if not ConfigManager.get_config_value('misc', 'hide_status_window'):
            self.status_window = StatusWindow()

        self.create_tray_icon()
        # Don't show main window - just tray icon
        # self.main_window.show()
        self.key_listener.start()  # Start listening immediately

    def create_tray_icon(self):
        """
        Create the system tray icon and its context menu.
        """
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(project_root, 'assets', 'ww-logo.png')
        self.tray_icon = QSystemTrayIcon(QIcon(icon_path), self.app)

        tray_menu = QMenu()

        show_action = QAction('WhisperWriter Main Menu', self.app)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)

        settings_action = QAction('Open Settings', self.app)
        settings_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(settings_action)

        exit_action = QAction('Exit', self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def cleanup(self):
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()

    def exit_app(self):
        """
        Exit the application.
        """
        self.cleanup()
        QApplication.quit()

    def restart_app(self):
        """Restart the application to apply the new settings."""
        # Update Windows startup based on setting
        start_with_windows = ConfigManager.get_config_value('misc', 'start_with_windows')
        manage_windows_startup(start_with_windows if start_with_windows is not None else True)

        self.cleanup()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_settings_closed(self):
        """
        If settings is closed without saving on first run, initialize the components with default values.
        """
        if not os.path.exists(os.path.join('src', 'config.yaml')):
            QMessageBox.information(
                self.settings_window,
                'Using Default Values',
                'Settings closed without saving. Default values are being used.'
            )
            self.initialize_components()

    def on_activation(self):
        """
        Called when the activation key combination is pressed.
        """
        print(">>> on_activation called")

        # Block activations while processing transcription
        if self._processing_transcription:
            print(">>> Ignoring activation (processing transcription)")
            return

        # Cooldown check - ignore activations within 1 second of last transcription
        if time.time() - self._last_transcription_time < 1.0:
            print(">>> Ignoring activation (cooldown)")
            return

        if self.result_thread and self.result_thread.isRunning():
            print(">>> Recording in progress, stopping...")
            recording_mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
            if recording_mode == 'press_to_toggle':
                self.result_thread.stop_recording()
            elif recording_mode == 'continuous':
                self.stop_result_thread()
            return

        print(">>> Starting new recording")
        self.start_result_thread()

    def on_deactivation(self):
        """
        Called when the activation key combination is released.
        """
        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'hold_to_record':
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()
        else:
            # Start any-key listener now that hotkey is released
            if self.result_thread and self.result_thread.isRunning():
                self._start_any_key_listener()

    def start_result_thread(self):
        """
        Start the result thread to record audio and transcribe it.
        """
        if self.result_thread and self.result_thread.isRunning():
            return

        # Play start sound (non-blocking)
        if ConfigManager.get_config_value('misc', 'noise_on_start'):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sound_path = os.path.join(project_root, 'assets', 'start.wav')
            try:
                self._start_sound = AudioPlayer(sound_path)  # Keep reference
                self._start_sound.play(block=False)
            except Exception as e:
                print(f"Error playing start sound: {e}")

        self.result_thread = ResultThread(self.local_model)
        if not ConfigManager.get_config_value('misc', 'hide_status_window'):
            self.result_thread.statusSignal.connect(self.status_window.updateStatus)
            self.status_window.closeSignal.connect(self.stop_result_thread)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.start()


    def stop_result_thread(self):
        """
        Stop the result thread.
        """
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()

    def _start_any_key_listener(self):
        """Start listening for any key press to stop recording."""
        if self._any_key_listener:
            return

        def on_any_key_press(key):
            # Ignore modifier keys (Ctrl, Shift, Alt, etc.)
            if key in (Key.ctrl_l, Key.ctrl_r, Key.shift_l, Key.shift_r,
                       Key.alt_l, Key.alt_r, Key.cmd_l, Key.cmd_r):
                return True  # Don't suppress modifier keys
            print(f">>> Any key pressed: {key} - stopping recording (key suppressed)")
            self._stop_any_key_listener()
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()
            return False  # Suppress the key - don't send it to the system

        def on_any_key_release(key):
            # Always allow key releases to pass through
            return True

        # suppress=True allows us to block keys from reaching other apps
        self._any_key_listener = KeyboardListener(
            on_press=on_any_key_press,
            on_release=on_any_key_release,
            suppress=True
        )
        self._any_key_listener.start()

    def _stop_any_key_listener(self):
        """Stop the any key listener."""
        if self._any_key_listener:
            self._any_key_listener.stop()
            self._any_key_listener = None

    def on_transcription_complete(self, result):
        """
        When the transcription is complete, type the result and start listening for the activation key again.
        """
        # Block any activations during processing
        self._processing_transcription = True

        # Stop the any-key listener
        self._stop_any_key_listener()

        # Stop key listener to prevent Ctrl+V from triggering hotkey
        self.key_listener.stop()

        # Play completion sound (non-blocking to not delay key listener restart)
        if ConfigManager.get_config_value('misc', 'noise_on_completion'):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sound_path = os.path.join(project_root, 'assets', 'beep.wav')
            try:
                self._completion_sound = AudioPlayer(sound_path)  # Keep reference to prevent GC
                self._completion_sound.play(block=False)
            except Exception as e:
                print(f"Error playing completion sound: {e}")

        # Check output settings
        copy_to_clipboard = ConfigManager.get_config_value('output', 'copy_to_clipboard')
        auto_type = ConfigManager.get_config_value('output', 'auto_type')

        if copy_to_clipboard:
            try:
                import pyperclip
                from pynput.keyboard import Controller, Key
                import time

                pyperclip.copy(result)
                print(f"Copied to clipboard: {result}")

                # Auto-paste with Ctrl+V
                time.sleep(0.1)
                keyboard = Controller()
                keyboard.press(Key.ctrl)
                keyboard.press('v')
                time.sleep(0.05)
                keyboard.release('v')
                keyboard.release(Key.ctrl)
                time.sleep(0.1)
                print("Auto-pasted with Ctrl+V")
            except Exception as e:
                print(f"Error copying/pasting: {e}")

        if auto_type:
            self.input_simulator.typewrite(result)

        # Set cooldown timestamp before restarting listener
        self._last_transcription_time = time.time()

        # Restart key listener after paste is done
        time.sleep(0.5)  # Longer delay to ensure all keys are released

        # Clear processing flag before restarting listener
        self._processing_transcription = False

        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'continuous':
            self.start_result_thread()
        else:
            self.key_listener.start()
            print("Key listener restarted - ready for next recording")

    def run(self):
        """
        Start the application.
        """
        sys.exit(self.app.exec_())


if __name__ == '__main__':
    app = WhisperWriterApp()
    app.run()
