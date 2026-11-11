"""
2_train.py — Fine-tuning de ASR quechua con Whisper-tiny.

Cumple el reglamento de entrega:
  - Lee los datos EXCLUSIVAMENTE desde ./data/ (generada por 1_setup_data.py).
  - Implementa LIMITE DE RECURSOS para no exceder la maquina del profesor:
        GPU Quadro P2000 -> 5 GB VRAM ; RAM 62 GB ; CUDA 13.0.
    Se usa Whisper-tiny (39M), batch pequeno, fp16 en GPU y un tope explicito de
    fraccion de VRAM. Si no hay GPU, hace fallback a CPU automaticamente.
  - Exporta el modelo entrenado y las metricas a ./outputs/.

Uso:
    python3 2_train.py

Variables de entorno opcionales (para ajustar sin tocar el codigo):
    MAX_TRAIN_SAMPLES   limita nº de ejemplos de entrenamiento (def. 200)
    MAX_STEPS           nº maximo de pasos de entrenamiento       (def. 100)
    BATCH_SIZE          tamano de lote por dispositivo            (def. 4)
    VRAM_FRACTION       fraccion de VRAM a usar como tope         (def. 0.30 ~ 5 GB)
"""

import json
import os
from pathlib import Path

import torch

# ----------------------------------------------------------------------------
# CONFIGURACION Y RUTAS (relativas)
# ----------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"

MODEL_NAME = "openai/whisper-tiny"
LANGUAGE = "quechua"          # idioma objetivo (Whisper lo mapea internamente)
TASK = "transcribe"
SAMPLING_RATE = 16000

MAX_TRAIN_SAMPLES = int(os.environ.get("MAX_TRAIN_SAMPLES", "200"))
MAX_STEPS = int(os.environ.get("MAX_STEPS", "100"))
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "4"))
VRAM_FRACTION = float(os.environ.get("VRAM_FRACTION", "0.30"))  # ~5 GB de una GPU de 16 GB


def configurar_dispositivo():
    """Detecta GPU/CPU y fija el tope de VRAM para respetar los 5 GB del profesor."""
    if torch.cuda.is_available():
        device = "cuda"
        # Tope explicito de VRAM: no usar mas de VRAM_FRACTION de la memoria de la GPU.
        torch.cuda.set_per_process_memory_fraction(VRAM_FRACTION, 0)
        total_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"GPU detectada: {torch.cuda.get_device_name(0)} ({total_gb:.1f} GB)")
        print(f"Tope de VRAM fijado al {VRAM_FRACTION*100:.0f}% (~{total_gb*VRAM_FRACTION:.1f} GB)")
        usar_fp16 = True
    else:
        device = "cpu"
        # En CPU limitamos los hilos para no saturar la maquina.
        torch.set_num_threads(min(4, os.cpu_count() or 4))
        print("Sin GPU: se entrena en CPU (mas lento). fp16 desactivado.")
        usar_fp16 = False
    return device, usar_fp16


def cargar_dataset():
    """Carga ./data/metadata.csv como un Dataset de audio de Hugging Face."""
    import pandas as pd
    from datasets import Audio, Dataset

    # Localiza metadata.csv (puede venir dentro de una subcarpeta del comprimido).
    candidatos = list(DATA_DIR.rglob("metadata.csv"))
    if not candidatos:
        raise FileNotFoundError(
            "No se encontro ./data/metadata.csv. Ejecuta primero: python3 1_setup_data.py"
        )
    meta_path = candidatos[0]
    base = meta_path.parent  # las rutas de audio son relativas a esta carpeta

    df = pd.read_csv(meta_path)
    if not {"audio_path", "text"}.issubset(df.columns):
        raise ValueError("metadata.csv debe tener las columnas: audio_path,text")

    # Convierte audio_path (relativa) en ruta absoluta en disco para que datasets la lea.
    df["audio"] = df["audio_path"].apply(lambda p: str((base / p).resolve()))
    df = df[["audio", "text"]].head(MAX_TRAIN_SAMPLES)

    ds = Dataset.from_pandas(df, preserve_index=False)
    ds = ds.cast_column("audio", Audio(sampling_rate=SAMPLING_RATE))
    print(f"Dataset cargado: {len(ds)} ejemplos (tope MAX_TRAIN_SAMPLES={MAX_TRAIN_SAMPLES}).")
    return ds


def main():
    from dataclasses import dataclass
    from typing import Any, Dict, List

    import evaluate
    from transformers import (
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        WhisperForConditionalGeneration,
        WhisperProcessor,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    device, usar_fp16 = configurar_dispositivo()

    # ----- Procesador y modelo -----
    print(f"Cargando modelo {MODEL_NAME} ...")
    processor = WhisperProcessor.from_pretrained(MODEL_NAME, language=LANGUAGE, task=TASK)
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
    model.generation_config.language = LANGUAGE
    model.generation_config.task = TASK
    model.generation_config.forced_decoder_ids = None

    # ----- Dataset -----
    ds = cargar_dataset()

    def preparar(batch):
        audio = batch["audio"]
        batch["input_features"] = processor.feature_extractor(
            audio["array"], sampling_rate=audio["sampling_rate"]
        ).input_features[0]
        batch["labels"] = processor.tokenizer(batch["text"]).input_ids
        return batch

    ds = ds.map(preparar, remove_columns=ds.column_names, desc="Extrayendo features")

    # ----- Collator -----
    @dataclass
    class DataCollatorSpeechSeq2Seq:
        processor: Any

        def __call__(self, features: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
            input_features = [{"input_features": f["input_features"]} for f in features]
            batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
            label_features = [{"input_ids": f["labels"]} for f in features]
            labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
            labels = labels_batch["input_ids"].masked_fill(
                labels_batch.attention_mask.ne(1), -100
            )
            if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
                labels = labels[:, 1:]
            batch["labels"] = labels
            return batch

    collator = DataCollatorSpeechSeq2Seq(processor=processor)

    # ----- Metrica WER -----
    metric = evaluate.load("wer")

    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)
        wer = 100 * metric.compute(predictions=pred_str, references=label_str)
        return {"wer": wer}

    # ----- Argumentos de entrenamiento (recursos limitados) -----
    args = Seq2SeqTrainingArguments(
        output_dir=str(OUTPUT_DIR / "checkpoints"),
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=2,
        learning_rate=1e-4,
        warmup_steps=10,
        max_steps=MAX_STEPS,
        gradient_checkpointing=True,   # ahorra VRAM
        fp16=usar_fp16,
        logging_steps=10,
        save_steps=MAX_STEPS,
        save_total_limit=1,
        report_to=[],                  # sin wandb/tensorboard
        remove_unused_columns=False,
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=ds,
        data_collator=collator,
        compute_metrics=compute_metrics,
        tokenizer=processor.feature_extractor,
    )

    print("Iniciando entrenamiento...")
    resultado = trainer.train()

    # ----- Exportar modelo y metricas a ./outputs/ -----
    print("Guardando modelo y metricas en ./outputs/ ...")
    model.save_pretrained(OUTPUT_DIR / "modelo_quechua_asr")
    processor.save_pretrained(OUTPUT_DIR / "modelo_quechua_asr")

    metricas = {
        "modelo": MODEL_NAME,
        "dispositivo": device,
        "ejemplos_entrenamiento": len(ds),
        "max_steps": MAX_STEPS,
        "batch_size": BATCH_SIZE,
        "train_loss": float(resultado.training_loss),
        "runtime_segundos": float(resultado.metrics.get("train_runtime", 0.0)),
    }
    with open(OUTPUT_DIR / "metricas.json", "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    print("Listo. Resultados en ./outputs/")
    print(json.dumps(metricas, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
