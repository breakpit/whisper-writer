Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Transcript\whisper-writer"
WshShell.Run "C:\Transcript\whisper-writer\venv\Scripts\pythonw.exe run.py", 0, False
