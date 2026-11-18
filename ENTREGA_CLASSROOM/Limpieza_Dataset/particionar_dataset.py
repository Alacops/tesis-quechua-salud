"""
particionar_dataset.py — Partición train/val/test SIN FUGA DE DATOS y normalización.

Es el paso que convierte `dataset_limpio.csv` en un dataset *entrenable con rigor*.
Resuelve las dos amenazas que el EDA solo había DETECTADO:

  AMENAZA 1 — Fuga por hablante.
     1 hablante aporta el 8,9 % de los clips. Si su voz cae a la vez en train y test,
     el modelo "reconoce la voz", no el idioma -> WER artificialmente bajo.
     SOLUCIÓN: partición DISJUNTA POR HABLANTE (ningún client_id cruza de split).

  AMENAZA 2 — Fuga por frase.
     2 067 frases únicas se grabaron ~11 veces. Si la misma frase aparece en train y
     test, el modelo la memoriza en vez de generalizar.

HALLAZGO (medido abajo): en este corpus los dos ejes son INCOMPATIBLES. Como casi
todos los hablantes graban las mismas ~2 058 frases, una partición disjunta por
hablante deja el 100 % de las frases de test también en train, y viceversa. No se
puede ser disjunto en ambos ejes sin quedarse sin datos. Por eso el script genera
LAS DOS particiones y MIDE el trade-off de cada una, en lugar de esconderlo:

  - split_speaker  : disjunto por hablante (mide fuga de FRASES que queda).
  - split_sentence : disjunto por frase    (mide fuga de HABLANTES que queda).

RECOMENDACIÓN para el ASR médico (ver reporte): priorizar `split_sentence`, porque el
sistema debe transcribir FRASES NUEVAS dichas en consulta; evitar que el modelo
memorice las 2 058 frases fijas del corpus es más importante que la disyunción de voz.

Además aplica la normalización ortográfica (normalizar_texto.py): añade `sentence_norm`
y marca las filas con dígitos (`has_digit`), ambiguas para el ASR.

Reproducibilidad: SEED fija, sin dependencias fuera de pandas/numpy.
Uso:
    python particionar_dataset.py
Salida:
    dataset_particionado.csv   (dataset_limpio + sentence_norm, has_digit, split)
    reporte_particion.txt      (verificación de disyunción y fuga medida)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from normalizar_texto import normalizar_quechua, tiene_digitos

SEED = 42
AQUI = Path(__file__).resolve().parent
ENTRADA = AQUI / "dataset_limpio.csv"
SALIDA = AQUI / "dataset_particionado.csv"
REPORTE = AQUI / "reporte_particion.txt"

# Proporciones objetivo MEDIDAS EN CLIPS (no en número de hablantes).
P_TEST = 0.10
P_VAL = 0.10
# el resto (0.80) es train.

_log: list[str] = []


def log(msg: str = "") -> None:
    print(msg)
    _log.append(msg)


def asignar_split_por_grupo(df: pd.DataFrame, col_grupo: str) -> pd.Series:
    """Asigna cada grupo entero (hablante o frase) a un split; objetivo en nº de clips.

    Algoritmo determinista: se baraja el orden de los grupos con la semilla fija y se
    les va asignando codiciosamente a test, luego a val, hasta alcanzar la proporción
    de CLIPS deseada; el resto va a train. Así ningún grupo se parte entre splits.
    """
    tam = df.groupby(col_grupo).size()                    # clips por grupo
    grupos = tam.sample(frac=1.0, random_state=SEED).index.tolist()  # barajados
    total = int(tam.sum())
    objetivo_test = P_TEST * total
    objetivo_val = P_VAL * total

    split_de = {}
    acum_test = acum_val = 0
    for g in grupos:
        n = int(tam[g])
        if acum_test < objetivo_test:
            split_de[g] = "test"
            acum_test += n
        elif acum_val < objetivo_val:
            split_de[g] = "val"
            acum_val += n
        else:
            split_de[g] = "train"
    return df[col_grupo].map(split_de)


def fuga(df: pd.DataFrame, col_split: str, col_grupo: str, a: str, b: str) -> tuple[int, int, float]:
    """Nº de clips del split `b` cuyo valor de `col_grupo` también está en el split `a`."""
    grupos_a = set(df.loc[df[col_split] == a, col_grupo])
    mask_b = df[col_split] == b
    comparten = df.loc[mask_b, col_grupo].isin(grupos_a)
    n_b = int(mask_b.sum())
    n_comp = int(comparten.sum())
    pct = 100.0 * n_comp / n_b if n_b else 0.0
    return n_comp, n_b, pct


def verificar(df: pd.DataFrame, col_split: str, col_disjunta: str, col_fuga: str) -> None:
    """Reporta: distribución, disyunción del eje elegido y fuga del otro eje."""
    resumen = df.groupby(col_split).agg(
        clips=("path", "size"),
        hablantes=("client_id", "nunique"),
        frases=("sentence_norm", "nunique"),
    ).reindex(["train", "val", "test"])
    resumen["clips_%"] = (100 * resumen["clips"] / len(df)).round(1)
    for s, fila in resumen.iterrows():
        log(f"    {s:5} : {int(fila['clips']):6d} clips ({fila['clips_%']:4.1f}%)  "
            f"| {int(fila['hablantes']):3d} hablantes | {int(fila['frases']):4d} frases")

    cruces = int((df.groupby(col_disjunta)[col_split].nunique() > 1).sum())
    nombre_disj = "hablante" if col_disjunta == "client_id" else "frase"
    estado = f"OK — ningún {nombre_disj} cruza de split" if cruces == 0 \
        else f"FALLO — {cruces} {nombre_disj}s cruzan"
    log(f"    disyunción por {nombre_disj}: {estado}")

    nombre_fuga = "frases" if col_fuga == "sentence_norm" else "hablantes"
    log(f"    fuga de {nombre_fuga} que queda (val/test que también están en train):")
    for b in ("val", "test"):
        n_comp, n_b, pct = fuga(df, col_split, col_fuga, "train", b)
        log(f"        {b:4} : {n_comp}/{n_b} clips ({pct:.1f}%)")


def main() -> None:
    if not ENTRADA.exists():
        raise SystemExit(f"No se encontró {ENTRADA}. Ejecuta antes eda_limpieza.py.")

    df = pd.read_csv(ENTRADA)
    log(f"Entrada: {ENTRADA.name}  ->  {df.shape[0]} filas x {df.shape[1]} columnas")

    # --- Normalización ortográfica ---
    df["sentence_norm"] = df["sentence"].astype(str).map(normalizar_quechua)
    df["has_digit"] = df["sentence"].astype(str).map(tiene_digitos)
    n_dig = int(df["has_digit"].sum())
    n_cambiadas = int((df["sentence"].astype(str) != df["sentence_norm"]).sum())
    log("")
    log("NORMALIZACIÓN DE TEXTO (normalizar_texto.py)")
    log(f"  Filas cuyo texto cambió al normalizar : {n_cambiadas} ({100*n_cambiadas/len(df):.1f}%)")
    log(f"  Filas con dígitos (texto ambiguo)      : {n_dig} ({100*n_dig/len(df):.1f}%)")
    log(f"  Frases únicas: crudas={df['sentence'].nunique()} -> normalizadas={df['sentence_norm'].nunique()}")

    # --- DOS particiones, una por cada eje de fuga ---
    df["split_speaker"] = asignar_split_por_grupo(df, "client_id")
    df["split_sentence"] = asignar_split_por_grupo(df, "sentence_norm")

    log("")
    log("PARTICIÓN A — disjunta por HABLANTE (split_speaker)")
    verificar(df, "split_speaker", col_disjunta="client_id", col_fuga="sentence_norm")

    log("")
    log("PARTICIÓN B — disjunta por FRASE (split_sentence)")
    verificar(df, "split_sentence", col_disjunta="sentence_norm", col_fuga="client_id")

    log("")
    log("LECTURA DEL TRADE-OFF")
    log("  - split_speaker evita que el modelo 'reconozca la voz', pero deja ~100% de")
    log("    las frases de test también en train (memorización de frases posible).")
    log("  - split_sentence evita la memorización de las 2 058 frases fijas, a costa de")
    log("    que algunas voces aparezcan en train y test.")
    log("  RECOMENDACIÓN (ASR médico): usar `split_sentence` como partición principal,")
    log("  porque el sistema debe transcribir FRASES NUEVAS en consulta; reportar el")
    log("  solapamiento de hablantes como limitación. Mantener `split_speaker` para una")
    log("  evaluación complementaria de robustez ante voces no vistas.")

    # Guardar.
    df.to_csv(SALIDA, index=False, encoding="utf-8")
    log("")
    log(f"Escrito: {SALIDA.name}  ({df.shape[0]} filas x {df.shape[1]} columnas)")
    REPORTE.write_text("\n".join(_log) + "\n", encoding="utf-8")
    log(f"Reporte: {REPORTE.name}")


if __name__ == "__main__":
    main()
