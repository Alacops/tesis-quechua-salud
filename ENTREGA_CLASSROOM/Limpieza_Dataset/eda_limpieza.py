"""
eda_limpieza.py — Exploración y limpieza del dataset (Protocolo EDA del Detective).

Aplica el protocolo de 5 pasos / 8 herramientas del material del curso
(Msc. Raúl Huillca Huallparimachi, "Exploración y limpieza de un dataset"):

    Paso 0  El Primer Vistazo    -> head / info / describe
    Paso 1  La Escena del Crimen -> nulos, duplicados, errores obvios (LIMPIEZA)
    Paso 2  Anatomía Numérica    -> histograma + caja y bigotes (Box plot) + barras
    Paso 3  Conexiones Ocultas   -> dispersión + Pearson + Spearman + mapa de calor
    Paso 4  La Variable Objetivo -> gráficos cruzados

Dataset: Common Voice 27.0, variedad quechua sureño (qxp) — subconjunto `validated`.
Es el corpus base del Proyecto IA (ASR quechua) de la tesis.

RIGUROSIDAD:
  - Metodológica : orden estricto de los pasos; cada decisión de limpieza se toma
                   sobre evidencia numérica, no sobre supuestos.
  - Teórica      : se usan Pearson (lineal) y Spearman (monótona, robusta) de forma
                   complementaria; outliers por regla IQR (Tukey).
  - Interpretativa: cada figura se acompaña de una lectura (ver informe).
  - Replicabilidad: semilla fija, versiones registradas, rutas autodescubiertas,
                   salidas deterministas (figuras/ y dataset_limpio.csv).

Uso:
    python eda_limpieza.py
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # backend sin pantalla: reproducible en cualquier máquina
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats

# ---------------------------------------------------------------------------
# 0. CONFIGURACIÓN Y REPRODUCIBILIDAD
# ---------------------------------------------------------------------------
SEED = 42
np.random.seed(SEED)

AQUI = Path(__file__).resolve().parent
PROYECTO_IA = AQUI.parent.parent / "03_Proyecto_IA"
FIG_DIR = AQUI / "figuras"
FIG_DIR.mkdir(exist_ok=True)
SALIDA_LIMPIO = AQUI / "dataset_limpio.csv"
RESUMEN_TXT = AQUI / "resumen_eda.txt"

# Paleta del proyecto: rampa azul -> turquesa -> verde (coherente en toda la tesis).
PALETA = ["#17365d", "#1f6fb2", "#2aa8a8", "#38bf8f", "#7fd16b"]
CMAP_AV = LinearSegmentedColormap.from_list("azulverde", PALETA)
plt.rcParams.update({
    "figure.dpi": 110,
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "axes.axisbelow": True,
})

NUMERICAS = ["dur_s", "n_chars", "n_words", "cps", "up_votes", "down_votes", "net_votes"]
_log: list[str] = []


def log(msg: str = "") -> None:
    """Imprime y acumula para el resumen en disco."""
    print(msg)
    _log.append(msg)


# ---------------------------------------------------------------------------
# CARGA Y DERIVACIÓN DE VARIABLES
# ---------------------------------------------------------------------------
def localizar_tsv() -> tuple[Path, Path]:
    tsvs = list(PROYECTO_IA.rglob("validated.tsv"))
    if not tsvs:
        sys.exit("ERROR: no se encontró 'validated.tsv' bajo 03_Proyecto_IA. "
                 "Descomprime el corpus Common Voice (qxp) allí.")
    validated = tsvs[0]
    dur = validated.parent / "clip_durations.tsv"
    return validated, dur


def cargar() -> pd.DataFrame:
    validated, dur = localizar_tsv()
    df = pd.read_csv(validated, sep="\t", low_memory=False)
    cd = pd.read_csv(dur, sep="\t")
    cd.columns = ["path", "dur_ms"]
    df = df.merge(cd, on="path", how="left")
    # Variables derivadas (features de forma del habla, útiles para ASR)
    df["dur_s"] = df["dur_ms"] / 1000.0
    df["n_chars"] = df["sentence"].str.len()
    df["n_words"] = df["sentence"].str.split().apply(len)
    df["cps"] = df["n_chars"] / df["dur_s"]            # velocidad de habla (car/seg)
    df["net_votes"] = df["up_votes"] - df["down_votes"]
    return df


# ---------------------------------------------------------------------------
# PASO 0 — EL PRIMER VISTAZO
# ---------------------------------------------------------------------------
def paso0(df: pd.DataFrame) -> None:
    log("\n" + "=" * 70)
    log("PASO 0 — EL PRIMER VISTAZO (head / info / describe)")
    log("=" * 70)
    log(f"Forma del dataset: {df.shape[0]} filas x {df.shape[1]} columnas")
    log("\n-- df.info() (tipos y no-nulos) --")
    buf = io.StringIO()
    df.info(buf=buf)
    log(buf.getvalue())
    log("\n-- df.describe() numéricas --")
    log(df[NUMERICAS].describe().round(2).to_string())


# ---------------------------------------------------------------------------
# PASO 1 — LA ESCENA DEL CRIMEN (nulos, duplicados, errores) + LIMPIEZA
# ---------------------------------------------------------------------------
def paso1(df: pd.DataFrame) -> pd.DataFrame:
    log("\n" + "=" * 70)
    log("PASO 1 — LA ESCENA DEL CRIMEN (calidad: nulos, duplicados, errores)")
    log("=" * 70)

    # --- Nulos ---
    nulos = df.isna().sum()
    pct = (nulos / len(df) * 100).round(1)
    tabla_nulos = pd.DataFrame({"nulos": nulos, "pct": pct})
    log("\n-- Nulos por columna --")
    log(tabla_nulos.to_string())

    # Figura 1: % de nulos por columna
    cols = tabla_nulos[tabla_nulos.pct > 0].sort_values("pct")
    fig, ax = plt.subplots(figsize=(7, 4))
    colores = [PALETA[0] if p < 50 else PALETA[2] for p in cols.pct]
    ax.barh(cols.index, cols.pct, color=colores, edgecolor="white")
    for y, p in enumerate(cols.pct):
        ax.text(p + 1, y, f"{p}%", va="center", fontsize=8)
    ax.set_xlabel("% de valores faltantes")
    ax.set_title("Paso 1 · Mapa de nulos (columnas con faltantes)")
    ax.set_xlim(0, 105)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig1_nulos.png", bbox_inches="tight")
    plt.close(fig)

    # --- Duplicados ---
    dup_filas = df.duplicated().sum()
    dup_path = df["path"].duplicated().sum()
    frases_unicas = df["sentence"].nunique()
    log(f"\n-- Duplicados --")
    log(f"Filas idénticas completas : {dup_filas}")
    log(f"Rutas de audio repetidas  : {dup_path}")
    log(f"Frases únicas / total     : {frases_unicas} / {len(df)} "
        f"(cada frase se grabó ~{len(df)/frases_unicas:.0f} veces)")
    log("  -> Repetir una frase NO es un error (es multi-hablante), pero obliga a")
    log("     particionar por frase/hablante para evitar fuga de datos en train/test.")

    # --- Errores obvios ---
    # (a) sentence_domain es multi-etiqueta con comas; algunas filas repiten tokens.
    dom = df["sentence_domain"].fillna("unknown")
    tokens = dom.str.split(",")
    df["_dom_malformado"] = tokens.apply(lambda t: len(t) != len(set(x.strip() for x in t)))
    n_malform = int(df["_dom_malformado"].sum())
    # (b) clips de baja calidad: rechazos >= aceptaciones (net<=0)
    n_netneg = int((df["net_votes"] <= 0).sum())
    log(f"\n-- Errores obvios --")
    log(f"Filas con 'sentence_domain' malformado (tokens repetidos): {n_malform}")
    log(f"Clips con net_votes <= 0 (rechazos >= aceptaciones)      : {n_netneg}")

    # --- LIMPIEZA (decisiones justificadas) ---
    log("\n-- LIMPIEZA aplicada --")
    antes = df.shape

    # 1) Eliminar columnas sin información.
    const_cols = [c for c in df.columns if df[c].nunique(dropna=True) <= 1]
    vacias = [c for c in ["variant", "segment"] if c in df.columns]
    a_borrar = sorted(set(const_cols) | set(vacias) | {"sentence_id", "_dom_malformado"})
    a_borrar = [c for c in a_borrar if c in df.columns]
    log(f"1) Columnas eliminadas (vacías/constantes/redundantes): {a_borrar}")
    # locale es constante 'qxp' -> entra por const_cols. Guardamos el flag antes de borrar.
    malform_flag = df["_dom_malformado"].copy()

    # 2) Normalizar sentence_domain: deduplicar tokens, extraer señales útiles.
    dom_norm = tokens.apply(lambda t: sorted(set(x.strip() for x in t)))
    df["domains"] = dom_norm.apply(lambda t: ";".join(t))
    df["n_domains"] = dom_norm.apply(len)
    df["is_healthcare"] = dom_norm.apply(lambda t: int("healthcare" in t))
    log(f"2) 'sentence_domain' normalizado -> domains / n_domains / is_healthcare "
        f"({n_malform} filas con tokens duplicados corregidas).")

    # 3) Nulos categóricos demográficos -> categoría explícita 'unknown'
    #    (no se imputan ni se borran: el audio+texto siguen siendo válidos para ASR).
    for c in ["age", "gender", "accents"]:
        if c in df.columns:
            df[c] = df[c].fillna("unknown")
    log("3) Nulos en age/gender/accents -> 'unknown' (metadato demográfico no "
        "invalida el clip; borrar perdería hasta 63% del corpus).")

    df = df.drop(columns=a_borrar)

    # 4) Marcar outliers por IQR (Tukey) en dur_s y cps — se FLAGEA, no se borra aún,
    #    para no perder señal sin justificación visual (ver Paso 2).
    def fences(s: pd.Series) -> tuple[float, float]:
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        return q1 - 1.5 * iqr, q3 + 1.5 * iqr

    lo_d, hi_d = fences(df["dur_s"])
    lo_c, hi_c = fences(df["cps"])
    df["is_outlier"] = (((df["dur_s"] < lo_d) | (df["dur_s"] > hi_d)) |
                        ((df["cps"] < lo_c) | (df["cps"] > hi_c))).astype(int)
    df["malformado_origen"] = malform_flag.astype(int).values
    n_out = int(df["is_outlier"].sum())
    log(f"4) Outliers marcados por IQR en dur_s [{lo_d:.2f},{hi_d:.2f}] y "
        f"cps [{lo_c:.2f},{hi_c:.2f}]: {n_out} filas ({n_out/len(df)*100:.1f}%).")

    log(f"\nForma antes={antes} -> después={df.shape} "
        f"(columnas depuradas; filas conservadas, outliers marcados).")
    return df


# ---------------------------------------------------------------------------
# PASO 2 — ANATOMÍA NUMÉRICA (histograma + box plot + barras)
# ---------------------------------------------------------------------------
def paso2(df: pd.DataFrame) -> None:
    log("\n" + "=" * 70)
    log("PASO 2 — ANATOMÍA NUMÉRICA (una variable a la vez)")
    log("=" * 70)

    vistas = ["dur_s", "n_chars", "cps", "net_votes"]
    etiquetas = {"dur_s": "Duración (s)", "n_chars": "Long. frase (car.)",
                 "cps": "Velocidad (car/s)", "net_votes": "Votos netos"}

    # Figura 2: histogramas
    fig, axs = plt.subplots(2, 2, figsize=(10, 6.5))
    for ax, c in zip(axs.ravel(), vistas):
        ax.hist(df[c], bins=40, color=PALETA[1], edgecolor="white")
        ax.axvline(df[c].mean(), color=PALETA[4], lw=2, label=f"media={df[c].mean():.2f}")
        ax.axvline(df[c].median(), color=PALETA[0], lw=2, ls="--",
                   label=f"mediana={df[c].median():.2f}")
        ax.set_title(etiquetas[c]); ax.legend(fontsize=7)
    fig.suptitle("Paso 2 · Histogramas (¿cómo se reparten los datos?)", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_histogramas.png", bbox_inches="tight")
    plt.close(fig)

    # Figura 3: box plots (caja y bigotes) -> outliers
    fig, axs = plt.subplots(1, 4, figsize=(11, 4))
    for ax, c in zip(axs, vistas):
        bp = ax.boxplot(df[c], vert=True, patch_artist=True, widths=0.6,
                        flierprops=dict(marker="o", markersize=3,
                                        markerfacecolor=PALETA[4], alpha=0.4))
        bp["boxes"][0].set(facecolor=PALETA[2], alpha=0.7)
        bp["medians"][0].set(color=PALETA[0], lw=2)
        ax.set_title(etiquetas[c]); ax.set_xticks([])
    fig.suptitle("Paso 2 · Caja y bigotes (mediana, dispersión y outliers)", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_boxplots.png", bbox_inches="tight")
    plt.close(fig)

    # Figura 4: barras de categóricas (desbalance)
    fig, axs = plt.subplots(2, 2, figsize=(11, 7))
    _barras(axs[0, 0], df["gender"], "Género (desbalance severo)")
    _barras(axs[0, 1], df["age"], "Rango de edad")
    _barras(axs[1, 0], df["is_healthcare"].map({1: "healthcare", 0: "otros"}),
            "¿Dominio salud? (relevante a la tesis)")
    # clips por hablante (concentración)
    vc = df["client_id"].value_counts()
    axs[1, 1].bar(range(len(vc)), vc.values, color=PALETA[1])
    axs[1, 1].set_title(f"Clips por hablante ({len(vc)} hablantes)")
    axs[1, 1].set_xlabel("hablante (ordenado)"); axs[1, 1].set_ylabel("n.º de clips")
    axs[1, 1].axhline(vc.median(), color=PALETA[4], ls="--",
                      label=f"mediana={int(vc.median())}")
    axs[1, 1].legend(fontsize=8)
    fig.suptitle("Paso 2 · Variables categóricas (¿está balanceado el dataset?)", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_barras_categoricas.png", bbox_inches="tight")
    plt.close(fig)

    log("Figuras 2-4 generadas (histogramas, box plots, barras categóricas).")
    log(f"  gender: {dict(df['gender'].value_counts())}")
    log(f"  concentración hablantes: 1 hablante aporta {vc.max()} clips "
        f"({vc.max()/len(df)*100:.1f}% del total).")


def _barras(ax, serie: pd.Series, titulo: str) -> None:
    vc = serie.value_counts()
    ax.bar(vc.index.astype(str), vc.values,
           color=[PALETA[i % len(PALETA)] for i in range(len(vc))], edgecolor="white")
    for i, v in enumerate(vc.values):
        ax.text(i, v, f"{v}", ha="center", va="bottom", fontsize=8)
    ax.set_title(titulo)
    ax.tick_params(axis="x", rotation=20)


# ---------------------------------------------------------------------------
# PASO 3 — CONEXIONES OCULTAS (dispersión + Pearson/Spearman + heatmap)
# ---------------------------------------------------------------------------
def paso3(df: pd.DataFrame) -> None:
    log("\n" + "=" * 70)
    log("PASO 3 — CONEXIONES OCULTAS (dos variables: correlación)")
    log("=" * 70)

    cols = ["dur_s", "n_chars", "n_words", "cps", "up_votes", "down_votes", "net_votes"]
    sub = df[cols]

    # Dispersión clave: longitud de frase vs duración (+ Pearson y Spearman)
    r_p, _ = stats.pearsonr(df["n_chars"], df["dur_s"])
    r_s, _ = stats.spearmanr(df["n_chars"], df["dur_s"])
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.6))
    axs[0].scatter(df["n_chars"], df["dur_s"], s=6, alpha=0.25, color=PALETA[1])
    axs[0].set_xlabel("Longitud de la frase (caracteres)")
    axs[0].set_ylabel("Duración del audio (s)")
    axs[0].set_title(f"n_chars vs dur_s\nPearson={r_p:.2f} · Spearman={r_s:.2f}")
    # Dispersión que revela el 'engaño de los números': cps vs duración
    r_p2, _ = stats.pearsonr(df["cps"], df["dur_s"])
    r_s2, _ = stats.spearmanr(df["cps"], df["dur_s"])
    axs[1].scatter(df["dur_s"], df["cps"], s=6, alpha=0.25, color=PALETA[2])
    axs[1].set_xlabel("Duración del audio (s)")
    axs[1].set_ylabel("Velocidad (car/s)")
    axs[1].set_title(f"dur_s vs cps\nPearson={r_p2:.2f} · Spearman={r_s2:.2f}")
    fig.suptitle("Paso 3 · Diagramas de dispersión (¿se mueven juntas?)", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig5_dispersion.png", bbox_inches="tight")
    plt.close(fig)

    # Mapas de calor: Pearson (lineal) y Spearman (monótona/robusta)
    corr_p = sub.corr(method="pearson")
    corr_s = sub.corr(method="spearman")
    fig, axs = plt.subplots(1, 2, figsize=(13, 5.3))
    for ax, corr, nombre in [(axs[0], corr_p, "Pearson (lineal)"),
                             (axs[1], corr_s, "Spearman (monótona, robusta)")]:
        im = ax.imshow(corr, vmin=-1, vmax=1, cmap=CMAP_AV)
        ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=45, ha="right")
        ax.set_yticks(range(len(cols))); ax.set_yticklabels(cols)
        for i in range(len(cols)):
            for j in range(len(cols)):
                v = corr.iloc[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=7, color="white" if abs(v) > 0.55 else "black")
        ax.set_title(nombre)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("Paso 3 · Matriz de calor de correlaciones", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_heatmaps.png", bbox_inches="tight")
    plt.close(fig)

    log(f"n_chars~dur_s  Pearson={r_p:.2f}  Spearman={r_s:.2f}")
    log(f"dur_s~cps      Pearson={r_p2:.2f}  Spearman={r_s2:.2f}")
    log("Figura 6 (heatmaps Pearson/Spearman) generada.")


# ---------------------------------------------------------------------------
# PASO 4 — LA VARIABLE OBJETIVO (gráficos cruzados)
# ---------------------------------------------------------------------------
def paso4(df: pd.DataFrame) -> None:
    log("\n" + "=" * 70)
    log("PASO 4 — LA VARIABLE OBJETIVO (is_healthcare: foco de la tesis)")
    log("=" * 70)

    df = df.copy()
    df["grupo"] = df["is_healthcare"].map({1: "salud", 0: "otros"})
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.6))
    for ax, c, t in [(axs[0], "dur_s", "Duración (s)"),
                     (axs[1], "n_chars", "Long. frase (car.)"),
                     (axs[2], "cps", "Velocidad (car/s)")]:
        datos = [df[df.grupo == g][c].values for g in ["salud", "otros"]]
        bp = ax.boxplot(datos, labels=["salud", "otros"], patch_artist=True, widths=0.6)
        for b, col in zip(bp["boxes"], [PALETA[2], PALETA[0]]):
            b.set(facecolor=col, alpha=0.7)
        for m in bp["medians"]:
            m.set(color="white", lw=2)
        ax.set_title(t)
    fig.suptitle("Paso 4 · Rasgos del subconjunto de salud vs. el resto", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig7_objetivo.png", bbox_inches="tight")
    plt.close(fig)

    # Contraste numérico: ¿el subconjunto de salud difiere? (Mann-Whitney, no param.)
    for c in ["dur_s", "n_chars", "cps"]:
        a = df[df.grupo == "salud"][c]
        b = df[df.grupo == "otros"][c]
        u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        log(f"{c:8s} salud(med={a.median():.2f}) vs otros(med={b.median():.2f}) "
            f"Mann-Whitney p={p:.3g}")
    log(f"Clips de salud: {(df.grupo=='salud').sum()} "
        f"({(df.grupo=='salud').mean()*100:.1f}% del corpus limpio).")


# ---------------------------------------------------------------------------
# ESCRITURA DEL DATASET LIMPIO (apto para entrenar)
# ---------------------------------------------------------------------------
def escribir_limpio(df: pd.DataFrame) -> None:
    log("\n" + "=" * 70)
    log("DATASET LIMPIO (apto para entrenar el ASR)")
    log("=" * 70)
    apto = df[(df["is_outlier"] == 0) & (df["net_votes"] > 0)].copy()
    cols_finales = ["client_id", "path", "sentence", "domains", "is_healthcare",
                    "n_domains", "age", "gender", "accents", "up_votes", "down_votes",
                    "net_votes", "dur_s", "n_chars", "n_words", "cps"]
    cols_finales = [c for c in cols_finales if c in apto.columns]
    apto = apto[cols_finales]
    apto.to_csv(SALIDA_LIMPIO, index=False, encoding="utf-8")
    log(f"Criterio de inclusión: sin outlier IQR (dur_s, cps) y net_votes>0.")
    log(f"Filas: {len(df)} (crudo validado) -> {len(apto)} (limpio) "
        f"[-{len(df)-len(apto)} filas, {(1-len(apto)/len(df))*100:.1f}%].")
    log(f"Escrito: {SALIDA_LIMPIO.name}  ({len(apto)} filas x {len(cols_finales)} col.)")


# ---------------------------------------------------------------------------
def main() -> None:
    log(f"Reproducibilidad: python={sys.version.split()[0]}  "
        f"pandas={pd.__version__}  numpy={np.__version__}  SEED={SEED}")
    df = cargar()
    paso0(df)
    df = paso1(df)
    paso2(df)
    paso3(df)
    paso4(df)
    escribir_limpio(df)
    RESUMEN_TXT.write_text("\n".join(_log), encoding="utf-8")
    log(f"\nResumen guardado en {RESUMEN_TXT.name}. Figuras en figuras/.")


if __name__ == "__main__":
    main()
