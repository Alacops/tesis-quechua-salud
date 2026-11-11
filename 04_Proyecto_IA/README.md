# Proyecto IA — Reconocimiento de voz (ASR) en quechua

## ¿Qué hace el modelo?

Realiza *fine-tuning* del modelo **Whisper-tiny** (OpenAI, ~39 millones de
parámetros) para **reconocimiento automático de voz (ASR) en quechua**: recibe un
audio hablado en quechua y produce su **transcripción en texto**. Es el componente
de entrada del pipeline de la tesis (ASR → traducción → síntesis de voz) orientado a
la comunicación médico–paciente.

El entrenamiento está acotado para ejecutarse dentro de los límites de hardware del
evaluador (GPU Quadro P2000, **5 GB de VRAM**; 62 GB de RAM; CUDA 13.0): se usa un
modelo pequeño, lotes reducidos, *gradient checkpointing*, precisión mixta (fp16) en
GPU y un **tope explícito de fracción de VRAM**. Si no hay GPU disponible, el código
hace *fallback* automático a CPU.

## Estructura de la entrega

```
1_setup_data.py     # Descarga el dataset desde Google Drive y lo deja en ./data/
2_train.py          # Entrena el modelo leyendo ./data/ y exporta a ./outputs/
requirements.txt    # Dependencias exactas (pip freeze)
README.md           # Este archivo
```

> El dataset **no** se incluye en el `.zip`. Se descarga automáticamente desde
> Google Drive al ejecutar `1_setup_data.py`.

## Cómo ejecutar

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python3 1_setup_data.py    # crea ./data/ con el dataset
python3 2_train.py         # entrena y crea ./outputs/
```

### Variables opcionales (ajuste de recursos)

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `MAX_TRAIN_SAMPLES` | Nº de ejemplos de entrenamiento | 200 |
| `MAX_STEPS` | Pasos máximos de entrenamiento | 100 |
| `BATCH_SIZE` | Tamaño de lote por dispositivo | 4 |
| `VRAM_FRACTION` | Fracción de VRAM como tope | 0.30 (~5 GB) |

## Tiempo estimado de ejecución

| Script | GPU (Quadro P2000, 5 GB) | CPU (sin GPU) |
|---|---|---|
| `1_setup_data.py` | 1–5 min (según tamaño del dataset y red) | igual |
| `2_train.py` (config por defecto: 100 pasos, 200 ejemplos) | ~5–10 min | ~20–40 min |

> Los tiempos son aproximados y dependen del tamaño real del dataset y de la
> conexión. La descarga de los pesos de Whisper-tiny (~150 MB) ocurre una sola vez.

## Salidas

Al terminar, en `./outputs/` se generan:

- `modelo_quechua_asr/` — modelo y procesador entrenados.
- `metricas.json` — métricas del entrenamiento (loss, dispositivo, tiempo, etc.).
