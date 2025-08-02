import sys
import subprocess
import os
import webbrowser  # Import webbrowser module
import signal  # Import signal module for stopping the script
from dateutil.relativedelta import relativedelta  # Import relativedelta

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "../requirements.txt"])
except Exception as e:
    print(f"Error installing requirements: {e}")
    sys.exit(1)

from gradio import Interface, File, Textbox, Button  # Import necessary components from gradio
import pandas as pd
from utils.process_data import get_scalar

print(f'All libraries imported.')