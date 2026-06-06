# 🎯 AutomatizaciónLeads — Prospector de Diseño Web

Sistema automatizado de prospección de clientes para freelancers de diseño web. Busca negocios locales en **Google Maps**, analiza su presencia digital y genera mensajes de WhatsApp personalizados listos para enviar, todo desde un dashboard visual en local.

---

## ✨ ¿Qué hace?

```
Google Maps → Análisis web → Scoring → Dashboard visual
```

1. **Scraping de Google Maps** con Playwright — extrae nombre, teléfono, email, web, reseñas y puntuación de cada negocio
2. **Análisis de presencia digital** — comprueba PageSpeed (móvil + escritorio), SSL, tecnología antigua
3. **Scoring automático** — puntúa del 1 al 10 la urgencia de mejorar su web (sin APIs de pago)
4. **Dashboard en `localhost:5050`** — visualiza todos los leads con filtros, copia mensajes de WhatsApp con un clic

---

## 🖥️ Demo

![Dashboard](https://img.shields.io/badge/Dashboard-localhost%3A5050-7c83ff?style=for-the-badge)

Cada lead muestra:
- 📞 Teléfono directo con enlace a WhatsApp
- ✉️ Email extraído automáticamente de su web
- 🌐 URL de la web (si tiene)
- 📊 Score PageSpeed móvil y escritorio
- 🔒 Estado SSL
- ⚠️ Si la web usa tecnología antigua
- 💬 Mensaje de WhatsApp personalizado listo para copiar

---

## 🚀 Instalación

### 1. Clona el repositorio

```bash
git clone git@github.com:Elmonfas/AutomatizacionLeads.git
cd AutomatizacionLeads
```

### 2. Instala las dependencias

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configura tu búsqueda

Edita `config.json`:

```json
{
  "search_query": "peluquería Ruzafa Valencia",
  "max_results": 10,
  "freelancer_name": "Pedro",
  "freelancer_city": "Valencia"
}
```

| Campo | Descripción |
|---|---|
| `search_query` | Sector + zona + ciudad (lo que escribirías en Google Maps) |
| `max_results` | Número de negocios a analizar (10–30 recomendado) |
| `freelancer_name` | Tu nombre — aparece en los mensajes de WhatsApp |
| `freelancer_city` | Tu ciudad — aparece en los mensajes de WhatsApp |

---

## ▶️ Uso

### Opción A — Todo en uno (recomendado)
```bash
python3 main.py
```
Ejecuta el scraping, analiza las webs, genera los scores y abre el dashboard automáticamente.

### Opción B — Solo el dashboard (con datos ya guardados)
```bash
python3 main.py --dashboard
```

---

## 📊 Dashboard

Abre **[http://localhost:5050](http://localhost:5050)** en tu navegador.

### Funcionalidades:
- **Filtros** por tipo (sin web / web mala / con web) y score mínimo
- **Búsqueda** en tiempo real por nombre
- **Ordenación** por score, rating de Google o número de reseñas
- **Copiar mensaje** — un clic copia el WhatsApp al portapapeles
- **Abrir WhatsApp** — si tiene teléfono, abre el chat directamente
- **Nueva búsqueda** — lanza el scraper desde la web con log de progreso en vivo

---

## 🧠 Criterios de scoring (1–10)

| Situación | Score |
|---|---|
| Sin web | **10** |
| Web con PageSpeed móvil < 30 | 8–9 |
| Sin SSL (HTTP) | +2 |
| Tecnología web antigua | +2 |
| Web no mobile-friendly | +1 |
| Web aceptable (>65) | 1–3 |

---

## 📁 Estructura del proyecto

```
AutomatizacionLeads/
├── main.py          # Orquestador principal
├── scraper.py       # Scraping de Google Maps con Playwright
├── analyzer.py      # Análisis PageSpeed + detección tecnología + emails
├── scorer.py        # Scoring heurístico + generación mensajes WhatsApp
├── app.py           # Dashboard Flask (localhost:5050)
├── config.json      # Configuración editable
├── requirements.txt # Dependencias Python
└── .env.example     # Variables de entorno opcionales
```

---

## 🔧 Variables de entorno (opcionales)

Copia `.env.example` a `.env`:

```bash
cp .env.example .env
```

```env
# Opcional — sin key funciona pero con cuota limitada
PAGESPEED_API_KEY=AIza...
```

> La API key de PageSpeed es **gratuita** con 25.000 llamadas/día. Consíguela en [Google Cloud Console](https://console.cloud.google.com).

---

## ⚡ Consejos de uso

- Cambia `search_query` cada día para cubrir distintos sectores: `"restaurante Malasaña Madrid"`, `"fontanero Sevilla"`, `"clínica dental Barcelona"`
- Con `max_results: 30` el scraping tarda ~15 min (delays anti-detección)
- Baja los delays a `1–2s` si quieres más velocidad (riesgo de bloqueo bajo)
- Los mensajes de WhatsApp están listos para copiar y pegar desde el dashboard

---

## 🛡️ Anti-detección

El scraper implementa varias técnicas para evitar bloqueos de Google Maps:

- User agents rotativos (Chrome, Firefox, Safari)
- Delays aleatorios entre peticiones
- Viewport y timezone de España configurados
- Oculta `navigator.webdriver`
- Acepta cookies automáticamente

---

## 📄 Licencia

MIT — úsalo, modifícalo y compártelo libremente.

---

<div align="center">
  Hecho para freelancers de diseño web 🚀
</div>
