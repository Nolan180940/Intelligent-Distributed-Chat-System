# PyInstaller spec for ICDS Chat Client
# Run: pyinstaller build.spec
# Output will be in dist/ICDS_Chat.exe

# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

project_root = Path('.')
block_cipher = None

a = Analysis(
    ['client/gui_client.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include .env.example as template
        ('.env.example', '.'),
        # Include server so EXE can auto-start it
        ('server/chat_server.py', 'server'),
        ('server/__init__.py', 'server'),
        ('utils/chat_utils.py', 'utils'),
        ('utils/__init__.py', 'utils'),
        ('config/settings.py', 'config'),
        ('config/__init__.py', 'config'),
        # Image output folder
        ('generated_images', 'generated_images'),
    ],
    hiddenimports=[
        'tkinter',
        'threading',
        'queue',
        'json',
        'socket',
        'select',
        'time',
        'os',
        'sys',
        'typing',
        'subprocess',
        'config.settings',
        'utils.chat_utils',
        'server.chat_server',
        'client.chat_client',
        'client.login_dialog',
        'bot.ai_bot',
        'bot.sentiment_analyzer',
        'bot.summary_generator',
        'bot.image_gen',
        'textblob',
        'openai',
        'requests',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='XChat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No terminal window (pure GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add icon path here if you have one
)
