"""
Clipboard manager with full format support using pywin32.
Allows saving and restoring clipboard contents including images, files, and formatted text.
"""

import win32clipboard
import win32con
import ctypes
from ctypes import wintypes


class ClipboardManager:
    """
    Manages clipboard operations with support for all clipboard formats.
    Allows saving the current clipboard state and restoring it later.
    """

    # Common clipboard formats
    FORMATS_TO_SAVE = [
        win32con.CF_UNICODETEXT,  # Unicode text
        win32con.CF_TEXT,          # ANSI text
        win32con.CF_HDROP,         # File list
        win32con.CF_DIB,           # Device-independent bitmap
        win32con.CF_DIBV5,         # DIB v5 (better color support)
        win32con.CF_BITMAP,        # Bitmap handle (may not persist)
    ]

    def __init__(self):
        self._saved_data = {}

    def save(self):
        """
        Save all clipboard contents that can be retrieved.
        Returns True if successful, False otherwise.
        """
        self._saved_data = {}

        try:
            win32clipboard.OpenClipboard()
            try:
                # Enumerate all available formats
                format_id = 0
                while True:
                    format_id = win32clipboard.EnumClipboardFormats(format_id)
                    if format_id == 0:
                        break

                    try:
                        # Try to get data for this format
                        data = win32clipboard.GetClipboardData(format_id)
                        self._saved_data[format_id] = data
                    except Exception:
                        # Some formats can't be retrieved (handles, etc.)
                        pass
            finally:
                win32clipboard.CloseClipboard()

            return True
        except Exception as e:
            print(f"Error saving clipboard: {e}")
            return False

    def restore(self):
        """
        Restore previously saved clipboard contents.
        Returns True if successful, False otherwise.
        """
        if not self._saved_data:
            return False

        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()

                # Restore in a specific order for best compatibility
                # Text formats first, then others
                priority_order = [
                    win32con.CF_UNICODETEXT,
                    win32con.CF_TEXT,
                    win32con.CF_HDROP,
                    win32con.CF_DIB,
                    win32con.CF_DIBV5,
                ]

                # Restore priority formats first
                for format_id in priority_order:
                    if format_id in self._saved_data:
                        try:
                            win32clipboard.SetClipboardData(format_id, self._saved_data[format_id])
                        except Exception:
                            pass

                # Restore remaining formats
                for format_id, data in self._saved_data.items():
                    if format_id not in priority_order:
                        try:
                            win32clipboard.SetClipboardData(format_id, data)
                        except Exception:
                            pass
            finally:
                win32clipboard.CloseClipboard()

            return True
        except Exception as e:
            print(f"Error restoring clipboard: {e}")
            return False

    def set_text(self, text):
        """
        Set text to clipboard.
        """
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            finally:
                win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            print(f"Error setting clipboard text: {e}")
            return False

    def has_saved_data(self):
        """Check if there is saved clipboard data."""
        return bool(self._saved_data)

    def clear_saved(self):
        """Clear saved clipboard data from memory."""
        self._saved_data = {}

    def get_format_names(self):
        """Get human-readable names of saved formats (for debugging)."""
        format_names = {
            win32con.CF_TEXT: "CF_TEXT",
            win32con.CF_UNICODETEXT: "CF_UNICODETEXT",
            win32con.CF_BITMAP: "CF_BITMAP",
            win32con.CF_DIB: "CF_DIB",
            win32con.CF_DIBV5: "CF_DIBV5",
            win32con.CF_HDROP: "CF_HDROP (Files)",
            win32con.CF_OEMTEXT: "CF_OEMTEXT",
        }

        return [format_names.get(f, f"Format {f}") for f in self._saved_data.keys()]
