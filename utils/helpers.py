import os

def ensure_output_folder(folder):
    os.makedirs(folder, exist_ok=True)
