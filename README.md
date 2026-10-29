# Tesis — Sistema bidireccional de traducción de voz Quechua–Español con IA preentrenada para consultas médicas en Cusco

**Autor:** Alain Armando Condori Contreras · **Asesor:** Mtro. Ing. Raúl Huillca Huallparimachi
**Escuela Profesional de Ingeniería Informática y de Sistemas — UNSAAC**
Curso: Seminario de Investigación II (2026-2)

Proyecto de tesis de desarrollo: un *pipeline* integrado **ASR + MT + TTS** (MMS para voz y NLLB
adaptado de `quy` a `quz`) para la comunicación médico-paciente con pacientes quechuahablantes,
validado con consultas simuladas. Documentos en LaTeX con citas **APA7**.

## Estructura

```
SEMINARIO_2/
├── preambulo.tex            # Configuración compartida (APA7, márgenes, gráficos)
├── referencias.bib          # Bibliografía núcleo (APA7)
├── logo_unsaac.png          # Logo institucional usado en las carátulas
├── 01_RSL/                  # Revisión sistemática: entrega + evidencia (PRISMA)
│   ├── rsl_articulo.tex/.pdf    # Artículo de la revisión (2 columnas, refs. numéricas)
│   ├── diapositivas_rsl.html/.pdf  # Diapositivas (5 slides)
│   ├── queries_busqueda.md     # Cadenas de búsqueda + conteos PRISMA
│   ├── cribado.md              # Cribado de estudios (inclusión/exclusión)
│   └── extraccion_datos.md     # Tabla de extracción de datos
└── 02_Plan_Tesis/
    ├── plan_tesis_expo.tex  # Plan de tesis (versión exposición, por capítulos) ← PRINCIPAL
    ├── plan_tesis_expo.pdf  # PDF compilado (documento de entrega)
    └── antecedentes.bib     # Fuentes de la revisión usadas en antecedentes
```

> Material de apoyo (exportaciones `.bib` de las bases, captura de Parsifal, PDFs de
> referencia y `Estructuracion_Tesis/`) se mantiene **local**, fuera del control de versiones.

El documento principal de entrega es **`02_Plan_Tesis/plan_tesis_expo.pdf`** (carátula UNSAAC,
5 capítulos: I Introducción en 6 bloques · II Marco teórico y estado del arte · III Metodología ·
IV Estudio de factibilidad · V Aspectos administrativos · anexos con matrices de consistencia).

## Compilación

Toolchain: **MiKTeX** (Windows). Como el `.bib` usa biblatex-apa, hay que correr `biber`:

```bash
cd 02_Plan_Tesis
pdflatex plan_tesis_expo
biber   plan_tesis_expo
pdflatex plan_tesis_expo
pdflatex plan_tesis_expo
```

> En VS Code con la extensión **LaTeX Workshop** la receta `pdflatex → biber → pdflatex → pdflatex`
> ya está configurada en `.vscode/settings.json`.

## Gráficos (vectoriales, editables)
- Barras de la problemática en Cusco (`pgfplots`).
- Diagrama de arquitectura ASR → MT → TTS (`tikz`).
- Diagrama de Gantt del cronograma por fases (`tikz`, rampa azul→turquesa→verde).
- Tablas de operacionalización, presupuesto y matrices de consistencia (`booktabs`).
