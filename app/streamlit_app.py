"""Default Streamlit entry point for the customer exploration lab."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('customer_app.py')),run_name='__main__')
