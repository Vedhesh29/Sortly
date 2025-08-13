from setuptools import setup

APP = ['main.py']  # Your main Python script
DATA_FILES = []    # Add any extra files/folders your app needs
OPTIONS = {
    'argv_emulation': True,
    'packages': [],  # List of Python packages your app imports
    'iconfile': 'icon.icns',  # Optional: path to Mac app icon
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
