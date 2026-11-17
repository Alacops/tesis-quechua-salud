# Exploración y limpieza de un dataset — Protocolo EDA del Detective

Entrega del curso **Seminario de Investigación II** (Msc. Raúl Huillca Huallparimachi).
Aplica el protocolo de **5 pasos / 8 herramientas** del material de clase al corpus
**Common Voice 27.0**, variedad quechua sureño (`qxp`), subconjunto `validated` —
el corpus base del Proyecto IA (ASR quechua) de la tesis.

## Protocolo aplicado

| Paso | Herramientas | Dónde |
|------|--------------|-------|
| **0 · Primer Vistazo** | `head`, `info`, `describe` | script / notebook |
| **1 · Escena del Crimen** | nulos, duplicados, errores → **limpieza** | `fig1_nulos.png` |
| **2 · Anatomía Numérica** | histograma, **caja y bigotes (Box)**, barras | `fig2`, `fig3`, `fig4` |
| **3 · Conexiones Ocultas** | dispersión, **Pearson**, **Spearman**, **mapa de calor** | `fig5`, `fig6` |
| **4 · Variable Objetivo** | gráficos cruzados (`is_healthcare`) | `fig7` |

## Archivos

- **`eda_limpieza.py`** — script reproducible; genera las 7 figuras, el `dataset_limpio.csv` y `resumen_eda.txt`.
- **`eda_limpieza.ipynb`** — notebook ejecutado (narrativa paso a paso con interpretación y salidas incrustadas).
- **`informe_eda.tex` / `informe_eda.pdf`** — informe formal (6 págs.) con las figuras y las 4 dimensiones de rigurosidad.
- **`figuras/`** — `fig1`…`fig7` en PNG.
- **`dataset_limpio.csv`** — 21 653 filas depuradas, aptas para entrenar.
- **`resumen_eda.txt`** — bitácora de la ejecución.

## Cómo reproducir

```bash
# Requiere: python 3.11+, pandas, numpy, matplotlib, scipy
#           y el corpus qxp descomprimido bajo ../../03_Proyecto_IA/
python eda_limpieza.py            # regenera figuras + dataset limpio + resumen
pdflatex informe_eda.tex          # (x2) genera el PDF
```

El script autodescubre el `validated.tsv` del corpus. Semilla fija `SEED=42`.

## Hallazgos principales

- **Columnas vacías**: `variant` y `segment` 100 % nulas; `accents` 63 %, `gender` 28 %.
- **Desbalance severo de género**: 16 079 `female` vs 308 `male` → sesgo del ASR a declarar.
- **Concentración de hablantes**: 1 de 77 aporta el 8,9 % de los clips.
- **Fuga potencial**: 2 067 frases únicas repetidas ~11 veces → partición por frase/hablante.
- **Dominio salud**: ~78 % de los clips → cobertura favorable a la tesis médica.
- **Correlaciones**: `n_chars`~`dur_s` = 0,71 (lineal); Pearson vs Spearman divergen en
  `down_votes`~`net_votes` (−0,37 vs −0,50): justifica usar ambas.
- **Limpieza**: 22 727 → **21 653** filas.
