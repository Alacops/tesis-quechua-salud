"""
1_setup_data.py — Descarga y preparacion del dataset de ASR quechua.

Cumple el reglamento de entrega:
  - Descarga el dataset desde Google Drive con gdown (ID configurable).
  - Lo descomprime (.zip o .tar.gz) y lo deja en la carpeta local ./data/.
  - Usa SOLO rutas relativas al directorio del proyecto (nada de C:/ ni /home/).

Estructura esperada DENTRO del comprimido (y por tanto en ./data/):
    data/
      metadata.csv        # columnas: audio_path,text
      audios/*.wav        # audios en 16 kHz mono (o cualquier sr; se re-muestrea en train)

Donde:
  - audio_path : ruta del .wav RELATIVA a la carpeta ./data/ (p. ej. audios/0001.wav)
  - text       : transcripcion en quechua de ese audio.

Uso:
    python3 1_setup_data.py
"""

import os
import sys
import tarfile
import zipfile
from pathlib import Path

# ----------------------------------------------------------------------------
# CONFIGURACION
# ----------------------------------------------------------------------------
# Pega aqui el ID de tu archivo comprimido en Google Drive.
# El enlace se ve asi:  https://drive.google.com/file/d/<ESTE_ES_EL_ID>/view
# Compartido como "Cualquier persona con el enlace puede verlo" (solo lector).
# Tambien se puede pasar por variable de entorno: DRIVE_FILE_ID=xxxx python3 1_setup_data.py
DRIVE_FILE_ID = os.environ.get("DRIVE_FILE_ID", "PEGA_AQUI_EL_ID_DE_DRIVE")

# Rutas relativas (NUNCA absolutas).
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
ARCHIVE_PATH = DATA_DIR / "dataset_descargado"  # la extension real se detecta al descargar


def descargar_desde_drive(file_id: str, destino: Path) -> Path:
    """Descarga el comprimido desde Google Drive usando gdown. Devuelve la ruta real."""
    try:
        import gdown
    except ImportError:
        sys.exit("ERROR: falta 'gdown'. Instalalo con: pip install gdown")

    destino.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://drive.google.com/uc?id={file_id}"
    print(f"[1/3] Descargando dataset desde Google Drive (id={file_id})...")
    # gdown detecta la extension real del archivo y la anade al nombre de salida.
    ruta_descargada = gdown.download(url, str(destino), quiet=False, fuzzy=True)
    if ruta_descargada is None or not Path(ruta_descargada).exists():
        sys.exit(
            "ERROR: la descarga fallo. Verifica que:\n"
            "  - El ID de Drive es correcto.\n"
            "  - El archivo esta compartido como 'Cualquier persona con el enlace'.\n"
        )
    return Path(ruta_descargada)


def descomprimir(archivo: Path, destino: Path) -> None:
    """Descomprime .zip o .tar.gz dentro de ./data/."""
    print(f"[2/3] Descomprimiendo {archivo.name} en {destino}/ ...")
    nombre = archivo.name.lower()
    if nombre.endswith(".zip"):
        with zipfile.ZipFile(archivo, "r") as z:
            z.extractall(destino)
    elif nombre.endswith((".tar.gz", ".tgz", ".tar")):
        modo = "r:gz" if nombre.endswith((".tar.gz", ".tgz")) else "r:"
        with tarfile.open(archivo, modo) as t:
            t.extractall(destino)
    else:
        print(f"  AVISO: '{archivo.name}' no parece comprimido; se deja tal cual.")


def verificar(destino: Path) -> None:
    """Comprueba que ./data/ tiene el metadata.csv esperado."""
    print("[3/3] Verificando estructura del dataset...")
    # El comprimido puede traer una carpeta raiz; buscamos metadata.csv en cualquier nivel.
    candidatos = list(destino.rglob("metadata.csv"))
    if not candidatos:
        print(
            "  AVISO: no se encontro 'metadata.csv' dentro de ./data/.\n"
            "  Asegurate de que tu comprimido incluya metadata.csv (columnas: audio_path,text)."
        )
    else:
        print(f"  OK: metadata.csv encontrado en {candidatos[0].relative_to(PROJECT_DIR)}")
    print("Listo. Dataset preparado en ./data/")


def main() -> None:
    if DRIVE_FILE_ID == "PEGA_AQUI_EL_ID_DE_DRIVE":
        sys.exit(
            "ERROR: configura DRIVE_FILE_ID con el ID de tu archivo en Google Drive "
            "(editando este script o con la variable de entorno DRIVE_FILE_ID)."
        )
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    archivo = descargar_desde_drive(DRIVE_FILE_ID, ARCHIVE_PATH)
    descomprimir(archivo, DATA_DIR)
    verificar(DATA_DIR)


if __name__ == "__main__":
    main()
