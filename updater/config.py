# Configuración del auto-updater
GITHUB_REPO = "MoisesVillar19/Sistema-Academia-Futbol"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_DOWNLOAD_URL = f"https://github.com/{GITHUB_REPO}/releases/download"

# Frecuencia de verificación (en horas)
FRECUENCIA_VERIFICACION_HORAS = 24

# Nombre del archivo ejecutable
APP_EXE_NAME = "AcademiaFutbol.exe"

# Si el usuario dice "no", no molestar hasta nueva versión
RECORDAR_RECHAZO = True

# Si app está en Program Files, preferir Setup silencioso (con UAC) vs ZIP
PREFER_SETUP_FOR_PROGRAMFILES = True
