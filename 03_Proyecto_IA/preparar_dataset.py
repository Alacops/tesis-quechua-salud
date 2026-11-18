"""
preparar_dataset.py — Construye el dataset pequeño del demo A PARTIR del dataset ya
limpio, normalizado y particionado (no del TSV crudo).

ESTE SCRIPT NO VA EN EL ZIP DE LA ENTREGA. Es un ayudante que se corre UNA sola vez
en tu máquina para construir el dataset que subirás a Google Drive.

CAMBIO IMPORTANTE (coherencia con el EDA del curso):
  Antes leía el `validated.tsv` CRUDO y volvía a colar outliers y texto sin normalizar.
  Ahora toma las filas de `dataset_particionado.csv` —ya depurado por IQR, con texto
  normalizado (`sentence_norm`) y con la partición anti-fuga `split_sentence`—, de modo
  que el DEMO y el ENTRENAMIENTO comparten exactamente la misma limpieza.

Qué hace:
  1. Localiza `dataset_particionado.csv` (del EDA) y la carpeta `clips/` del corpus.
  2. Selecciona N clips del split de entrenamiento, PRIORIZANDO el dominio de salud
     (is_healthcare) y SIN repetir frase (frases distintas = demo más informativo).
  3. Convierte cada .mp3 -> .wav 16 kHz mono con ffmpeg.
  4. Escribe metadata.csv con columnas:  audio_path,text   (text = sentence_norm).
  5. Empaqueta todo en dataset_quechua_asr.zip, listo para subir a Drive.

Requisitos: python3, pandas y ffmpeg instalados.
Uso:
    python3 preparar_dataset.py
Variables de entorno opcionales:
    N_SAMPLES   número total de clips a incluir         (def. 400)
    SPLIT       split de origen (train/val/test)         (def. train)
    SEED        semilla aleatoria para reproducibilidad  (def. 42)
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd

# ----------------------------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
REPO_DIR = PROJECT_DIR.parent
BUILD_DIR = PROJECT_DIR / "_build_dataset"
AUDIOS_DIR = BUILD_DIR / "audios"
METADATA_PATH = BUILD_DIR / "metadata.csv"
ZIP_PATH = PROJECT_DIR / "dataset_quechua_asr.zip"

N_SAMPLES = int(os.environ.get("N_SAMPLES", "400"))
SPLIT = os.environ.get("SPLIT", "train")
SEED = int(os.environ.get("SEED", "42"))

# Dónde buscar el dataset limpio producido por el EDA (ENTREGA_CLASSROOM) o una copia
# local. Se prefiere el particionado; si no está, se usa el limpio sin partición.
CSV_CANDIDATOS = [
    PROJECT_DIR / "dataset_particionado.csv",
    REPO_DIR / "ENTREGA_CLASSROOM" / "Limpieza_Dataset" / "dataset_particionado.csv",
    PROJECT_DIR / "dataset_limpio.csv",
    REPO_DIR / "ENTREGA_CLASSROOM" / "Limpieza_Dataset" / "dataset_limpio.csv",
]


def localizar_csv() -> Path:
    for ruta in CSV_CANDIDATOS:
        if ruta.exists():
            print(f"Dataset limpio localizado: {ruta}")
            return ruta
    sys.exit(
        "ERROR: no se encontró dataset_particionado.csv ni dataset_limpio.csv.\n"
        "Ejecuta antes el EDA del curso:\n"
        "  cd ENTREGA_CLASSROOM/Limpieza_Dataset && python eda_limpieza.py && python particionar_dataset.py"
    )


def localizar_clips() -> Path:
    """Encuentra la carpeta clips/ del corpus Common Voice descargado."""
    tsvs = list(PROJECT_DIR.rglob("validated.tsv"))
    for tsv in tsvs:
        clips = tsv.parent / "clips"
        if clips.is_dir():
            print(f"Carpeta de audios localizada: {clips}")
            return clips
    sys.exit(
        "ERROR: no se encontró la carpeta 'clips/' del corpus. Descomprime el corpus "
        "Common Voice (qxp) dentro de esta carpeta (03_Proyecto_IA)."
    )


def comprobar_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit("ERROR: falta 'ffmpeg'. Instálalo:  sudo apt install -y ffmpeg")


def seleccionar_filas(csv_path: Path) -> pd.DataFrame:
    """Selecciona N filas del split, priorizando salud y sin repetir frase."""
    df = pd.read_csv(csv_path)

    # Texto de referencia: usa la versión normalizada si existe.
    col_texto = "sentence_norm" if "sentence_norm" in df.columns else "sentence"

    # Filtra por split (si el CSV está particionado); si no, usa todo.
    col_split = "split_sentence" if "split_sentence" in df.columns else \
                ("split" if "split" in df.columns else None)
    if col_split:
        df = df[df[col_split] == SPLIT]
        print(f"Filas en split '{SPLIT}' ({col_split}): {len(df)}")

    # Una fila por frase (demo con frases distintas).
    df = df.drop_duplicates(subset=col_texto)

    # Prioriza salud.
    if "is_healthcare" in df.columns:
        salud = df[df["is_healthcare"] == True]           # noqa: E712
        otros = df[df["is_healthcare"] != True]            # noqa: E712
    else:
        salud, otros = df.iloc[0:0], df
    salud = salud.sample(frac=1.0, random_state=SEED)
    otros = otros.sample(frac=1.0, random_state=SEED)

    seleccion = pd.concat([salud, otros]).head(N_SAMPLES)
    n_salud = int(seleccion["is_healthcare"].sum()) if "is_healthcare" in seleccion else 0
    print(f"Seleccionadas {len(seleccion)} frases distintas "
          f"({n_salud} de salud + {len(seleccion) - n_salud} de relleno).")
    return seleccion.rename(columns={col_texto: "text"})[["path", "text"]]


def convertir_y_empaquetar(seleccion: pd.DataFrame, clips: Path) -> None:
    """Convierte mp3 -> wav 16 kHz mono y escribe metadata.csv + zip."""
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    AUDIOS_DIR.mkdir(parents=True)

    filas_meta = []
    total = len(seleccion)
    for i, (_, reg) in enumerate(seleccion.iterrows(), 1):
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

    pd.DataFrame(filas_meta, columns=["audio_path", "text"]).to_csv(
        METADATA_PATH, index=False, encoding="utf-8"
    )
    print(f"metadata.csv escrito con {len(filas_meta)} filas.")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(METADATA_PATH, "metadata.csv")
        for wav in sorted(AUDIOS_DIR.glob("*.wav")):
            z.write(wav, f"audios/{wav.name}")
    mb = ZIP_PATH.stat().st_size / 1e6
    print(f"\nLISTO -> {ZIP_PATH.name} ({mb:.1f} MB) con {len(filas_meta)} audios.")
    print("Súbelo a Google Drive ('Cualquier persona con el enlace') y copia el ID.")


def main() -> None:
    comprobar_ffmpeg()
    csv_path = localizar_csv()
    clips = localizar_clips()
    seleccion = seleccionar_filas(csv_path)
    if seleccion.empty:
        sys.exit("ERROR: no se seleccionó ninguna frase. Revisa el CSV/SPLIT.")
    convertir_y_empaquetar(seleccion, clips)


if __name__ == "__main__":
    main()
