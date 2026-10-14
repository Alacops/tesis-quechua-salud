# Tabla de extracción de datos — Revisión sistemática

**Fecha:** 14/10/2026 · **Estudios:** 30 a texto completo (26 incluidos ✅ + 4 por confirmar 🔎)
**Mapeo a preguntas:** Tipo→RQ1 · Arquitectura/Corpus→RQ2 · Métricas→RQ3 · ¿Salud?→RQ4 · (limitaciones→RQ5, extraer del TC)

**Leyenda ¿Salud?:** *Potencial* = aplicable al diálogo clínico · *No* = dominio general · *Habilitador* = recurso que posibilita el sistema · *Bajo* = aporte clínico limitado.
**Celdas "por extraer (TC)"** = dato no disponible en el resumen; completar leyendo el texto completo.

---

## Síntesis de voz (TTS)

| Estudio | Variante | Arquitectura / técnica | Corpus / datos | Métricas → resultados | ¿Salud? |
|---------|----------|------------------------|----------------|-----------------------|---------|
| HuamanCuro2026 | Chanca (Ayacucho) | Tacotron 2+WaveNet, FastPitch+WaveGlow, VITS, **XTTS v2** (fine-tuning) | 2 300 grabaciones de alta calidad | MOS-N **4.9**, MOS-S **4.8**; F0 RMSE, SECS≈0.10 (XTTS v2 mejor) | Potencial |

## Reconocimiento de voz (ASR)

| Estudio | Variante | Arquitectura / técnica | Corpus / datos | Métricas → resultados | ¿Salud? |
|---------|----------|------------------------|----------------|-----------------------|---------|
| Zevallos202061 | Sureño | HMM / HTK, MFCC | Siminchikkunarayku | **WER 12.70 %** | Potencial |
| Zevallos20223518 | Bajo recurso | wav2letter++, aumento de datos (texto + voz sintética) | 99 h reales + 99 h sintéticas | **WER 22.75 %** (−8.73 % vs base) | Potencial |
| Chen20246444 | 6 lenguas indígenas (incl. quechua) | SSL (XLS-R / wav2vec 2.0) preentrenado | datos de bajo recurso | desempeño ASR — por extraer (TC) | Potencial |
| Romero2024 | Indígenas de América | Avances en ASR (revisión/experimental) | por extraer (TC) | por extraer (TC) | Potencial |
| Chuctaya201824 | — | MFCC + DTW + KNN (palabras aisladas) | números en quechua | exactitud — por extraer (TC) | Bajo (vocabulario mínimo) |

## Traducción automática (MT)

| Estudio | Variante | Arquitectura / técnica | Corpus / datos | Métricas → resultados | ¿Salud? |
|---------|----------|------------------------|----------------|-----------------------|---------|
| Ortega2020325 | QU–ES | RNN seq2seq + segmentación morfológica | corpus QU–ES | BLEU (mejora sobre baseline) | Potencial |
| Ebrahimi2024236 | 11 indígenas (incl. quechua) | Shared task; baselines Sheffield/Helsinki | datos AmericasNLP 2024 | **chrF++ +4.2** en quechua | No |
| Dhawan2026119 | Guarani, Quechua, Aymara | mBART fine-tune + datos sintéticos + normalización ortográfica | corpus + sintéticos | chrF++ (mejora con sintéticos) | No |
| Veliz2021241 | QU–ES | NMT; pretraining ES–EN + fine-tune | nuevos datos paralelos (poemas, letras, léxicos) | 1.º Track 2 / 3.º Track 1 (AmericasNLP) | No |
| Oncevay2021194 | 4 lenguas Perú (incl. quechua) | NMT multilingüe, subword, back-translation | ES–EN grande + monolingüe | desempeño multilingüe — por extraer (TC) | No |
| Chen202120 | Quechua, Indonesio | Segmentación **PRPE** | corpus paralelo QU–ES | BLEU (SOTA; supera modelos grandes) | No |
| Barbaran2026464 | ES–QU | opus-mt-es-en vs t5-small (fine-tune) | somosnlp-hackathon-2022 | **BLEU 15.47 · chrF 49.80** (opus-mt) | No |
| Ahmed2023156 | ES–QU | Preentrenado ES–EN vs ES–Finés + back-translation | literatura + dominio legal | Mejor con ES–Finés | No |
| Ebrahimi20233894 | QU–ES (y otras) | Alineadores Transformer preentrenados | alineamientos gold | evaluación extrínseca (NER, POS) | No |
| Gow-Smith2023192 | 11 indígenas (incl. quechua) | **NLLB-200** extendido + ensemble + back-translation | constituciones, noticias, manuales | **+11 % chrF** prom.; 1.º en 4 lenguas | No |
| Ortega202144 | Dos lenguas vecinas de bajo recurso | Combinación de lenguas vecinas | por extraer (TC) | por extraer (TC) | No |
| CuevaMedina2024 | Quechua → Español | Transformer + LMfusion + PRPE + **QuBERT** | datasets paralelos | por extraer; interfaz web | Potencial |
| Court20241332 🔎 | Bajo recurso | LLMs + retrieval | por extraer (TC) | 🔎 confirmar que evalúe quechua | No |
| Zheng2021234 🔎 | Bajo recurso | Cross-lingual LM pretraining | por extraer (TC) | 🔎 confirmar que evalúe quechua | No |
| Mohler20081228 🔎 | Low-density | BABYLON parallel text builder | textos paralelos | 🔎 confirmar que incluya quechua | No |
| Calderón-Ch.202663 🔎 | 9 idiomas (Andes) | Algoritmos adaptativos en microcontroladores | — | 🔎 confirmar componente quechua/voz | Potencial (contexto andino) |

## Traducción de voz (cascada ASR→MT / speech-to-text translation)

| Estudio | Variante | Arquitectura / técnica | Corpus / datos | Métricas → resultados | ¿Salud? |
|---------|----------|------------------------|----------------|-----------------------|---------|
| Ortega2023261 | QU → ES | Cascada ASR (XLS-R) + MT; Fairseq S2T | datos IWSLT 2023 | ~**16 BLEU** (unconstrained) | Potencial |
| Ortega2024173 | QU → ES | Fairseq S2T + **SpeechT5** + Whisper | IWSLT 2024 + web | **19.7 BLEU** | Potencial |
| Ortega2025260 | Collao | SpeechT5 fine-tune + transcripciones Collao | IWSLT 2025 + web | **26.7 BLEU** | Potencial |
| Ebrahimi2023217 | Indígenas (incl. quechua) | Shared task speech-to-text | datos AmericasNLP | por extraer (TC) | Potencial |
| Alvarez-Crespo2023837 | ES → QU | **Cascada**: ASR español + MT quechua (fine-tune desde NMT turco) + subtitulado | dataset público paralelo | BLEU/chrF (supera previos); validación con hablantes | Potencial (subtitulado en tiempo real) |

## Recursos (corpus, modelos, herramientas)

| Estudio | Variante | Aporte | Corpus / datos | Métricas → resultados | ¿Salud? |
|---------|----------|--------|----------------|-----------------------|---------|
| Zevallos20221 | Sureño | Corpus monolingüe + modelo **QuBERT** | corpus a gran escala | NER 71–74 % F1 · POS 84–87 % | Habilitador |
| Rios201691 | — | **Toolkit** básico de PLN (morfología, etc.) | — | por extraer (TC) | Habilitador |
| Guzman2021 (IEEE) | ES / QU | Plataforma web (WSDM/MVC) + API **Siminchikkunarayku** | corpus bilingüe ES/QU de voz (en construcción) | plataforma disponible | Potencial |

---

## Lecturas para tu propuesta (MMS + NLLB + cascada, quz, salud)

- **Arquitectura en cascada** ya probada en quechua: `Alvarez-Crespo2023837` (ES→QU subtitulado) y la serie **QUESPA** (`Ortega2023261/2024173/2025260`), que llega a **26.7 BLEU** en Collao — tu línea base natural.
- **TTS** de referencia: `HuamanCuro2026` (MOS ~4.9) — contrasta con tu propuesta MMS-TTS.
- **ASR** base: `Zevallos202061` (WER 12.70 %) y `Zevallos20223518` (aumento de datos).
- **Recursos** para el fine-tuning: QuBERT (`Zevallos20221`), toolkit (`Rios201691`), corpus de voz ES/QU (`Guzman2021`).
- **Vacío confirmado:** ninguno trabaja el **dominio médico-paciente** ni la variante **Cusco (quz)** de forma integrada → ese es tu aporte.
- **Pendiente antes de cerrar:** confirmar los **4 🔎** a texto completo (podrían subir los incluidos de 26 a 30).
