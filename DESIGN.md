---
name: TrazaAgro
description: Consola operativa de trazabilidad políglota e inocuidad para distribución de aguacate Hass.
colors:
  verde-bosque-aguacate: "#2D6A4F"
  verde-bosque-hover: "#245741"
  verde-bosque-tinte: "#E3F1E7"
  azul-tecnico-cedis: "#1D6996"
  azul-tecnico-tinte: "#E2EEF6"
  verde-brote: "#90BE6D"
  verde-brote-tinte: "#EAF4E0"
  carmesi-recall: "#A4161A"
  carmesi-recall-hover: "#871115"
  carmesi-tinte: "#FCE8E8"
  ambar-alerta: "#7A4F00"
  ambar-tinte: "#FFF3D1"
  papel-botanico: "#F1FAEE"
  superficie-blanca: "#FFFFFF"
  tinta-profunda: "#1B2A22"
  tinta-secundaria: "#46564D"
  borde-salvia: "#D3E2D0"
  borde-input: "#8FA597"
typography:
  headline:
    fontFamily: "Geist, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "24px"
    fontWeight: 650
    lineHeight: 1.25
  title:
    fontFamily: "Geist, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Geist, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Geist, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "0.06em"
  mono:
    fontFamily: "Geist Mono, ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    fontSize: "0.92em"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  xs: "6px"
  sm: "8px"
  md: "10px"
  lg: "12px"
  xl: "16px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  "2xl": "24px"
components:
  button-primary:
    backgroundColor: "{colors.verde-bosque-aguacate}"
    textColor: "{colors.superficie-blanca}"
    rounded: "{rounded.md}"
    padding: "9px 15px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "{colors.verde-bosque-hover}"
  button-secondary:
    backgroundColor: "{colors.superficie-blanca}"
    textColor: "{colors.azul-tecnico-cedis}"
    rounded: "{rounded.md}"
    padding: "9px 15px"
    height: "40px"
  button-secondary-hover:
    backgroundColor: "{colors.azul-tecnico-tinte}"
  button-danger:
    backgroundColor: "{colors.carmesi-recall}"
    textColor: "{colors.superficie-blanca}"
    rounded: "{rounded.md}"
    padding: "9px 15px"
    height: "40px"
  button-danger-hover:
    backgroundColor: "{colors.carmesi-recall-hover}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.azul-tecnico-cedis}"
    rounded: "{rounded.md}"
    padding: "6px 10px"
    height: "34px"
  card:
    backgroundColor: "{colors.superficie-blanca}"
    textColor: "{colors.tinta-profunda}"
    rounded: "{rounded.lg}"
    padding: "16px"
  input:
    backgroundColor: "{colors.superficie-blanca}"
    textColor: "{colors.tinta-profunda}"
    rounded: "{rounded.md}"
    padding: "9px 12px"
    height: "40px"
  badge-ok:
    backgroundColor: "{colors.verde-bosque-tinte}"
    textColor: "{colors.verde-bosque-aguacate}"
    rounded: "{rounded.pill}"
    padding: "3px 8px"
  badge-info:
    backgroundColor: "{colors.azul-tecnico-tinte}"
    textColor: "{colors.azul-tecnico-cedis}"
    rounded: "{rounded.pill}"
    padding: "3px 8px"
  badge-warn:
    backgroundColor: "{colors.ambar-tinte}"
    textColor: "{colors.ambar-alerta}"
    rounded: "{rounded.pill}"
    padding: "3px 8px"
  badge-bad:
    backgroundColor: "{colors.carmesi-tinte}"
    textColor: "{colors.carmesi-recall}"
    rounded: "{rounded.pill}"
    padding: "3px 8px"
---

# Design System: TrazaAgro

## Overview

**Creative North Star: "La Consola de Inocuidad Viva"**

TrazaAgro combina la precisión clínica de un instrumento de laboratorio con la cercanía orgánica del campo agrícola mexicano. El sistema opera sobre capas tonales suaves entre un lienzo papel botánico y tarjetas blancas puras delimitadas por bordes salvia nítidos, evitando por completo gradientes decorativos o efectos llamativos que distraigan de la lectura operativa.

La densidad es estructurada y escaneable: cada vista prioriza KPIs tabulares, tablas densas pero respirables, insignias de estado inequívocas (`Liberado`, `Bloqueado`) y nodos interactivos de trazabilidad física. La personalidad visual transmite rigor técnico, calma operativa y respuesta inmediata en escenarios de almacén, laboratorio y emergencia QA.

**Key Characteristics:**
- Capas tonales suaves entre lienzo botánico y superficie blanca pura, sin gradientes ni ornamentos.
- Semántica de color estricta donde verde, azul, ámbar y carmesí comunican estado operativo e inocuidad.
- Tipografía geométrica limpia (`Geist`) combinada con monoespaciado técnico (`Geist Mono`) para códigos de lote, operaciones y reglas de negocio (`RN-01` a `RN-11`).
- Contraste alto pensado para lectura rápida en escritorio (Electron y navegador web) bajo estándares WCAG AA.

## Colors

Una paleta orgánica y técnica de alto contraste donde cada acento cumple una función operativa precisa sobre fondos botánicos neutros.

### Primary
- **Verde Bosque Aguacate** (`verde-bosque-aguacate`): Identidad de marca, acciones principales de confirmación, pestaña activa y estados de lote `Liberado` u origen en el grafo. Su variante más profunda (`verde-bosque-hover`) responde al estado hover y su tinte suave (`verde-bosque-tinte`) respalda alertas e insignias positivas.

### Secondary
- **Azul Técnico CEDIS** (`azul-tecnico-cedis`): Enlaces, acciones secundarias, anillo de enfoque accesible (`:focus-visible`), referencias a reglas de negocio (`.rn`) y nodos de laboratorio o trazabilidad hacia atrás. Se acompaña de `azul-tecnico-tinte` para fondos informativos y hover secundario.

### Tertiary
- **Verde Brote** (`verde-brote`): Indicador de avance, barras de progreso, nodos de contaminación cruzada lateral en el visor de grafo y etiquetas de lotes recién cosechados junto con su tinte (`verde-brote-tinte`).

### Neutral & Semantic Status
- **Papel Botánico** (`papel-botanico`): Lienzo general de la aplicación y fondo de nodos base.
- **Superficie Blanca** (`superficie-blanca`): Tarjetas, barra superior, campos de entrada, modales y tabla de resumen.
- **Tinta Profunda** (`tinta-profunda`) y **Tinta Secundaria** (`tinta-secundaria`): Jerarquía de texto principal y metadatos/etiquetas con contraste legible.
- **Borde Salvia** (`borde-salvia`) y **Borde Input** (`borde-input`): Líneas divisorias estructurales de 1px y contorno de campos editables.
- **Carmesí Recall** (`carmesi-recall` / `carmesi-tinte`) y **Ámbar Alerta** (`ambar-alerta` / `ambar-tinte`): Reservados exclusivamente para bloqueos atómicos de emergencia, alertas críticas de inocuidad, nodos afectados en *recall* y advertencias de temperatura.

### Named Rules
**The Semantic Purity Rule.** El carmesí (`carmesi-recall`) y el ámbar (`ambar-alerta`) nunca se usan como decoración; su presencia indica exclusivamente riesgo sanitario, bloqueo activo o advertencia operativa.
**The Tonal Separation Rule.** La jerarquía entre fondo y contenedor se resuelve alternando `papel-botanico` y `superficie-blanca` con borde de 1px (`borde-salvia`), sin gradientes ni rellenos saturados de fondo.

## Typography

**Display / Body Font:** `"Geist"`, con respaldo del sistema (`system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`).
**Label / Mono Font:** `"Geist Mono"`, con respaldo monoespaciado (`ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace`).

**Character:** Neutra, geométrica y de alta legibilidad numérica (`tabular-nums` en KPIs, tablas y resúmenes), emparejada con monoespaciado técnico para distinguir de inmediato identificadores de lote, endpoints y reglas `RN`.

### Hierarchy
- **Headline** (`650`, `24px`, `1.25` line-height): Títulos principales de cada vista operativa (`h1`).
- **Title** (`600`, `16px`, `1.4` line-height): Encabezados de tarjetas, alertas y secciones (`h2`), con subtítulos de bloque en `14px` (`h3`).
- **Body** (`400`, `15px`, `1.5` line-height): Lectura general de formularios, tablas (`14px`) y listas operativas.
- **Label** (`600`, `12px`, `0.06em` tracking, mayúsculas): Sobretítulos (`.eyebrow`), encabezados de tabla (`th`) y metadatos de resumen (`dt`).
- **Mono** (`400`/`600`, `0.92em` / `11px` en chips `.op` y `.rn`): Códigos de lote, etiquetas de operación API y referencias a reglas de negocio.

### Named Rules
**The Tabular Data Rule.** Todo valor numérico en KPIs, tablas (`td.num`) y resúmenes (`dd`) debe usar `font-variant-numeric: tabular-nums` para alineación vertical exacta en auditorías.

## Layout

El contenedor principal (`main`) centra el área de trabajo hasta un máximo de `1220px` con relleno lateral de `20px` y respiración inferior de `56px`. La barra superior (`.topbar`) permanece fija (`sticky`) en la parte superior con relleno de `14px 20px`.

La retícula base usa `grid` con separación uniforme de `16px`. En móvil los bloques apilan en una columna (y `2` columnas para KPIs y resumen); a partir de `760px` se activan `4` columnas para KPIs, `5` columnas para resúmenes (`.summary`), `2fr 1fr` (`.two`) y `1fr 1fr` (`.half`). Las vistas de dispositivo/trazabilidad (`.device-wrap`, `.trace`) se expanden a `2` y `3` columnas a partir de `900px`.

## Elevation & Depth

El sistema es **plano por defecto con capas tonales suaves**. Las superficies en reposo no llevan sombra: el contraste entre `papel-botanico` y `superficie-blanca` más el borde de `1px` en `borde-salvia` definen cada contenedor.

### Shadow Vocabulary
- **Pestaña Activa** (`box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08)`): Eleva sutilmente la pestaña seleccionada sobre el riel de navegación.
- **Nodo Interactivo Hover** (`box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08)`): Respuesta táctil discreta al pasar el cursor sobre nodos del flujo de trazabilidad.
- **Marco de Dispositivo** (`box-shadow: 0 8px 24px rgba(27, 42, 34, 0.08)`): Sombra ambiental suave para vistas previas encapsuladas.
- **Modal Overlay** (`box-shadow: 0 20px 40px rgba(0, 0, 0, 0.18)`): Separación clara sobre el velo oscuro (`rgba(27, 42, 34, 0.48)`) en flujos transaccionales críticos.
- **Anillo de Enfoque** (`box-shadow: 0 0 0 3px #1D6996`): Contorno de accesibilidad de alto contraste en `:focus-visible`.

### Named Rules
**The Flat-By-Default Rule.** Las tarjetas, tablas y alertas en reposo son completamente planas; las sombras se reservan exclusivamente para overlays modales, pestaña activa o retroalimentación puntual de hover/focus.

## Shapes

Lenguaje geométrico amigable pero contenido: radios consistentes sin bordes afilados extremos ni curvas excesivas en contenedores grandes.
- Contenedores principales (`.card`, `.note`, `.alert`, `.summary`): radio estándar de `12px`.
- Controles interactivos (`.btn`, `.input`, `.tabs`, `.demo-card`): radio medio de `10px`.
- Elementos internos compactos (`.brand-mark`, `.tab`, `.flow .node`): radio suave de `8px` (`6px` en chips `.op`).
- Modales (`.modal-card`): radio amplio de `16px`.
- Insignias y barras de progreso (`.badge`, `.bar`, `.progress`): cápsula completa (`999px`).

## Components

Componentes funcionales, directos y sobrios, diseñados para minimizar errores en captura y consulta rápida.

### Buttons
- **Shape:** Bordes redondeados medios (`10px`), altura mínima táctil de `40px` (`34px` en `.btn-sm` y `.btn-ghost`, `50px` en `.btn-lg`).
- **Primary:** Fondo `verde-bosque-aguacate`, texto blanco, relleno `9px 15px`, peso `600`.
- **Hover / Focus:** Transición rápida de `0.15s` a `verde-bosque-hover`; enfoque con anillo `azul-tecnico-cedis` de `3px`.
- **Secondary / Danger / Ghost:** Secundario con fondo blanco, texto y borde `azul-tecnico-cedis` (hover a `azul-tecnico-tinte`); peligro en `carmesi-recall` para bloqueo de emergencia; ghost transparente para acciones auxiliares. Deshabilitado en gris salvia apagado (`#E7ECE8` / `#5B6660`).

### Chips & Badges
- **Style:** Cápsula (`999px`), relleno `3px 8px`, tipografía `12px` peso `600`.
- **Variants:** Semánticos sobre tinte suave con tinta de alto contraste: `.s-ok` (`verde-bosque-tinte` / `verde-bosque-aguacate`), `.s-info` (`azul-tecnico-tinte` / `azul-tecnico-cedis`), `.s-warn` (`ambar-tinte` / `ambar-alerta`), `.s-bad` (`carmesi-tinte` / `carmesi-recall`), `.s-new` (`verde-brote-tinte` / `#2F5216`) y `.s-mute`.

### Cards / Containers
- **Corner Style:** `12px` (`--radius`).
- **Background:** `superficie-blanca`.
- **Shadow Strategy:** Planas en reposo; sin sombra.
- **Border:** `1px solid` en `borde-salvia` (borde discontinuo en `.note`).
- **Internal Padding:** `16px` estándar (`12px 14px` en notas y celdas de `.summary`).

### Inputs / Fields
- **Style:** Fondo blanco puro, borde `1px solid` en `borde-input`, radio `10px`, altura mínima `40px`, relleno `9px 12px`.
- **Focus:** Anillo exterior de `3px` en `azul-tecnico-cedis`.
- **Labels:** Etiquetas de `13px` peso `600` encima del campo con separación de `6px`.

### Navigation
- **Style:** Barra superior fija (`.topbar`) en `superficie-blanca` con borde inferior `1px solid` en `borde-salvia`. Las pestañas (`.tabs`) viven dentro de una cápsula `papel-botanico` de radio `10px` con relleno de `4px`; la pestaña activa cambia a fondo blanco, texto `verde-bosque-aguacate` y sombra sutil de `1px`.

### Signature Component: Visor de Grafo y Tarjetas de Trazabilidad
- **Flow Nodes (`.flow .node`):** Nodos interactivos con radio `8px` y estados codificados por rol en la red Neo4j: `.origin` (verde), `.lab` (azul), `.store` (ámbar) y `.hot` (carmesi para puntos contaminados o en *recall*).
- **Trace Columns (`.trace .card`):** Tarjetas con acento superior de `4px` que diferencian de un vistazo la dirección del rastreo: hacia adelante (`.fwd` en carmesí), hacia atrás (`.back` en azul) y lateral/contagio cruzado (`.lat` en verde brote).

## Do's and Don'ts

### Do:
- **Do** mantener las superficies en capas tonales limpias (`papel-botanico` + `superficie-blanca` con borde `1px` en `borde-salvia`).
- **Do** usar `Geist Mono` con chips `.op` / `.rn` para códigos de lote y reglas de negocio, y `tabular-nums` en todo dato numérico.
- **Do** respetar la codificación semántica estricta (carmesí solo para bloqueo/recall, ámbar solo para advertencia/tienda, verde para liberado/origen, azul para técnico/lab).
- **Do** preservar el anillo `:focus-visible` de `3px` y alturas mínimas de `40px` en botones e inputs para cumplir WCAG AA.

### Don't:
- **Don't** introducir gradientes decorativos, glassmorphism o sombras pesadas en tarjetas de contenido en reposo.
- **Don't** mezclar colores de estado fuera de su significado operativo (por ejemplo, usar rojo/carmesí para botones de acción normal).
- **Don't** omitir bordes en tarjetas o inputs sobre fondos claros; la delimitación nítida es parte esencial de la legibilidad del sistema.
