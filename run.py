import os
import sys
import socket
from dotenv import load_dotenv

# Single instance check using a socket lock
def check_single_instance():
    """Prevent multiple instances by binding to a specific port."""
    lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Try to bind to localhost on a specific port
        lock_socket.bind(('127.0.0.1', 47200))
        return lock_socket  # Keep socket open to maintain lock
    except socket.error:
        print("WhisperWriter is already running!")
        sys.exit(0)

_instance_lock = check_single_instance()

# Add CUDA/cuDNN DLLs to PATH for GPU support
venv_path = os.path.dirname(os.path.abspath(__file__))
cuda_paths = [
    os.path.join(venv_path, 'venv', 'Lib', 'site-packages', 'nvidia', 'cudnn', 'bin'),
    os.path.join(venv_path, 'venv', 'Lib', 'site-packages', 'nvidia', 'cublas', 'bin'),
]
for cuda_path in cuda_paths:
    if os.path.exists(cuda_path):
        os.environ['PATH'] = cuda_path + os.pathsep + os.environ.get('PATH', '')

print('Starting WhisperWriter...')
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# CRITICAL: Load model BEFORE importing PyQt5 (ctranslate2/Qt DLL conflict on Windows)
print('Loading Whisper model (this may take a moment)...')
from utils import ConfigManager
from transcription import create_local_model

ConfigManager.initialize()
model_options = ConfigManager.get_config_section('model_options')

if not model_options.get('use_api'):
    preloaded_model = create_local_model()
else:
    preloaded_model = None

print('Model loaded. Starting UI...')

# NOW import and run the app (PyQt5 imports happen here)
from main import WhisperWriterApp

# Pass preloaded model to constructor
app = WhisperWriterApp(preloaded_model=preloaded_model)
app.run()
