import os
import shutil
import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime

# Pasta onde os arquivos serão salvos localmente
UPLOAD_FOLDER = "chat_uploads"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.sample_rate = 44100
        self.stream = None

    def start_recording(self):
        self.recording = True
        self.audio_data = []
        # Callback para capturar áudio em tempo real
        def callback(indata, frames, time, status):
            if self.recording:
                self.audio_data.append(indata.copy())
        
        self.stream = sd.InputStream(samplerate=self.sample_rate, channels=1, callback=callback)
        self.stream.start()

    def stop_recording(self):
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        
        if not self.audio_data:
            return None

        # Salvar arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{timestamp}.wav"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Juntar os pedaços de áudio e salvar
        my_recording = np.concatenate(self.audio_data, axis=0)
        sf.write(filepath, my_recording, self.sample_rate)
        
        return filepath

def save_attachment(source_path):
    """Copia um arquivo selecionado para a pasta do chat"""
    if not source_path: return None
    
    filename = os.path.basename(source_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Evitar nomes duplicados
    new_filename = f"{timestamp}_{filename}"
    destination = os.path.join(UPLOAD_FOLDER, new_filename)
    
    shutil.copy2(source_path, destination)
    return destination