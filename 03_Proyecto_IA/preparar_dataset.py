"""
preparar_dataset.py — Convierte el corpus Common Voice (qxp) al formato de la entrega.

ESTE SCRIPT NO VA EN EL ZIP DE LA ENTREGA. Es un ayudante que se corre UNA sola vez
en tu maquina para construir el dataset pequeno que subiras a Google Drive.

Que hace:
  1. Busca el validated.tsv del corpus Common Voice descargado (variedad qxp).
  2. Selecciona N clips, PRIORIZANDO los del dominio 'healthcare' (salud) por ser
     los mas relevantes para la tesis medica. Rellena el resto con clips variados.
  3. Convierte cada .mp3 -> .wav 16 kHz mono con ffmpeg (audio limpio y universal).
  4. Escribe metadata.csv con columnas:  audio_path,text
  5. Empaqueta todo en dataset_quechua_asr.zip, listo para subir a Drive.

Al descomprimirse en la maquina del profesor (via 1_setup_data.py) quedara como:
    data/
      metadata.csv
      audios/*.wav

Requisitos: python3 y ffmpeg instalados.
Uso:
    python3 preparar_dataset.py
Variables de entorno opcionales:
    N_SAMPLES       numero total de clips a incluir            (def. 400)
    PREFER_DOMAIN   dominio a priorizar                        (def. healthcare)
    MAX_CHARS       descarta frases mas largas que esto        (def. 150)
    SEED            semilla aleatoria para reproducibilidad     (def. 42)
"""

import csv
import os
import random
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# ----------------------------------------------------------------------------
# CONFIGURACION
# ----------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
BUILD_DIR = PROJECT_DIR / "_build_dataset"       # carpeta temporal de construccion
AUDIOS_DIR = BUILD_DIR / "audios"
METADATA_PATH = BUILD_DIR / "metadata.csv"
ZIP_PATH = PROJECT_DIR / "dataset_quechua_asr.zip"

N_SAMPLES = int(os.environ.get("N_SAMPLES", "400"))
PREFER_DOMAIN = os.environ.get("PREFER_DOMAIN", "healthcare")
MAX_CHARS = int(os.environ.get("MAX_CHARS", "150"))
SEED = int(os.environ.get("SEED", "42"))


def localizar_corpus() -> tuple[Path, Path]:
    """Encuentra validated.tsv y la carpeta clips/ del corpus descargado."""
    tsvs = list(PROJECT_DIR.rglob("validated.tsv"))
    if not tsvs:
        sys.exit(
            "ERROR: no se encontro 'validated.tsv'. Asegurate de haber descomprimido "
            "el corpus Common Voice dentro de esta carpeta (03_Proyecto_IA)."
        )
    validated = tsvs[0]
    clips = validated.parent / "clips"
    if not clips.is_dir():
        sys.exit(f"ERROR: no existe la carpeta de audios: {clips}")
    print(f"Corpus localizado:\n  tsv   = {validated}\n  clips = {clips}")
    return validated, clips


def comprobar_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit(
            "ERROR: falta 'ffmpeg'. Instalalo con:\n"
            "  (Ubuntu/WSL)  sudo apt install -y ffmpeg\n"
        )


def seleccionar_filas(validated: Path) -> list[dict]:
    """Lee el tsv y selecciona N filas, priorizando el dominio de salud."""
    preferidas, resto = [], []
    vistas = set()  # para no repetir la misma frase
    with open(validated, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f, delimiter="\t")
        for fila in lector:
            texto = (fila.get("sentence") or "").strip()
            if not texto or len(texto) > MAX_CHARS:
                continue
            if texto in vistas:
                continue
            vistas.add(texto)
            dominio = (fila.get("sentence_domain") or "").lower()
            registro = {"path": fila["path"], "text": texto}
            if PREFER_DOMAIN and PREFER_DOMAIN in dominio:
                preferidas.append(registro)
            else:
                resto.append(registro)

    rng = random.Random(SEED)
    rng.shuffle(preferidas)
    rng.shuffle(resto)

    seleccion = preferidas[:N_SAMPLES]
    if len(seleccion) < N_SAMPLES:
        seleccion += resto[: N_SAMPLES - len(seleccion)]

    print(
        f"Frases candidatas: {len(preferidas)} de '{PREFER_DOMAIN}' + {len(resto)} de otros.\n"
        f"Seleccionadas: {len(seleccion)} "
        f"({min(len(preferidas), N_SAMPLES)} de salud + "
        f"{max(0, len(seleccion) - min(len(preferidas), N_SAMPLES))} de relleno)."
    )
    return seleccion


def convertir_y_empaquetar(seleccion: list[dict], clips: Path) -> None:
    """Convierte mp3 -> wav 16 kHz mono y escribe metadata.csv."""
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    AUDIOS_DIR.mkdir(parents=True)

    filas_meta = []
    total = len(seleccion)
    for i, reg in enumerate(seleccion, 1):
        mp3 = clips / reg["path"]
        if not mp3.exists():
            continue
        stem = Path(reg["path"]).stem
        wav = AUDIOS_DIR / f"{stem}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", str(mp3), "-ar", "16000", "-ac", "1", str(wav)],
            check=True,
        )
        filas_meta.append({"audio_path": f"audios/{stem}.wav", "text": reg["text"]})
        if i % 50 == 0 or i == total:
            print(f"  convertidos {i}/{total}")

    with open(METADATA_PATH, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=["audio_path", "text"])
        escritor.writeheader()
        escritor.writerows(filas_meta)
    print(f"metadata.csv escrito con {len(filas_meta)} filas.")

    # Empaquetar: el zip contiene metadata.csv y audios/ en la raiz.
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(METADATA_PATH, "metadata.csv")
        for wav in sorted(AUDIOS_DIR.glob("*.wav")):
            z.write(wav, f"audios/{wav.name}")
    mb = ZIP_PATH.stat().st_size / 1e6
    print(f"\nLISTO -> {ZIP_PATH.name} ({mb:.1f} MB) con {len(filas_meta)} audios.")
    print("Subelo a Google Drive ('Cualquier persona con el enlace') y copia el ID.")


def main() -> None:
    comprobar_ffmpeg()
    validated, clips = localizar_corpus()
    seleccion = seleccionar_filas(validated)
    if not seleccion:
        sys.exit("ERROR: no se selecciono ninguna frase. Revisa el tsv.")
    convertir_y_empaquetar(seleccion, clips)


if __name__ == "__main__":
    main()
