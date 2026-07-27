from setuptools import setup

APP = ['browser.py']
OPTIONS = {
    'argv_emulation': True,
    'includes': ['PyQt6', 'PyQt6.QtWebEngineWidgets'],
    'packages': ['PyQt6'],
    'iconfile': 'LOGO.icns',
    'plist': {
        'CFBundleName': 'SimpleBrowser',
        'CFBundleDisplayName': 'SimpleBrowser',
        'CFBundleIdentifier': 'com.example.simplebrowser',
        'CFBundleShortVersionString': '1.0',
        'CFBundleVersion': '1.0.0',
    },
}

setup(
    app=APP,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
