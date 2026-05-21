# Suggestion FS Trento → MUSE con Fallback Gemini — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere il suggerimento "da FS - Trento a MUSE" al frontend e restituire una risposta hardcodata corretta quando Gemini è in rate limit.

**Architecture:** Il backend estende `get_fallback_response` per accettare il messaggio originale e selezionare il percorso di fallback (Trento FS → MUSE a piedi oppure Rovereto FS → MART in bici) in base al testo. La risposta include sempre `is_fallback: True`. Il frontend aggiunge la suggestion e mostra un disclaimer ⚠️ quando `is_fallback` è `true`.

**Tech Stack:** Python/FastAPI, pytest, pytest-asyncio, Vue 3, Axios.

---

## File map

| File | Azione | Responsabilità |
|---|---|---|
| `backend/ai/agent.py` | Modify | `get_fallback_response(message)` + `run_agent` passa `message` |
| `backend/tests/test_agent.py` | Modify | Test del routing per messaggio e propagazione `is_fallback` |
| `frontend/src/composables/useChat.js` | Modify | Propaga `is_fallback` dal response al messaggio |
| `frontend/src/components/ChatPanel.vue` | Modify | Nuova suggestion + rendering disclaimer + stile |

---

### Task 1: Backend — test fallback routing per messaggio

**Files:**
- Modify: `backend/tests/test_agent.py`

- [ ] **Step 1: Aggiungere import e tre test al fondo di `test_agent.py`**

Aprire `backend/tests/test_agent.py` e aggiungere in fondo:

```python
@pytest.mark.asyncio
async def test_fallback_muse_message_returns_trento_route():
    """Con messaggio contenente 'muse', il fallback usa Trento FS → MUSE."""
    with patch("ai.agent.get_route", new_callable=AsyncMock) as mock_route:
        mock_route.return_value = {
            "geojson": {"type": "LineString", "coordinates": []},
            "distance_m": 2000,
            "duration_s": 1500,
        }
        result = await get_fallback_response("da FS trento a MUSE")

    labels = [m["label"] for m in result["markers"]]
    assert any("MUSE" in l or "Trento" in l for l in labels)
    assert result["is_fallback"] is True
    assert "MUSE" in result["reply"]
    assert len(result["chips"]) == 3  # tempo, distanza, CO₂


@pytest.mark.asyncio
async def test_fallback_default_message_returns_rovereto_route():
    """Senza keyword MUSE, il fallback usa Rovereto FS → MART (comportamento esistente)."""
    with patch("ai.agent.get_route", new_callable=AsyncMock) as mock_route:
        mock_route.return_value = {
            "geojson": {"type": "LineString", "coordinates": []},
            "distance_m": 1200,
            "duration_s": 360,
        }
        result = await get_fallback_response("")

    labels = [m["label"] for m in result["markers"]]
    assert any("Rovereto" in l or "MART" in l for l in labels)
    assert result["is_fallback"] is True


@pytest.mark.asyncio
async def test_fallback_muse_ors_failure_returns_hardcoded_chips():
    """Se ORS fallisce nel fallback MUSE, i chips hardcoded vengono usati (non lista vuota)."""
    with patch("ai.agent.get_route", new_callable=AsyncMock) as mock_route:
        mock_route.side_effect = Exception("ORS non disponibile")
        result = await get_fallback_response("voglio andare al museo delle scienze")

    assert result["is_fallback"] is True
    assert len(result["chips"]) == 3  # tempo, distanza, CO₂ hardcoded
    assert result["route"] is None
```

Aggiungere `get_fallback_response` agli import in cima al file (riga 4):

```python
from ai.agent import execute_tool, build_chips, get_fallback_response
```

- [ ] **Step 2: Eseguire i test per verificare che falliscano**

```bash
cd /home/fallenangel/projects/CassandraRosmini/backend
pytest tests/test_agent.py::test_fallback_muse_message_returns_trento_route tests/test_agent.py::test_fallback_default_message_returns_rovereto_route tests/test_agent.py::test_fallback_muse_ors_failure_returns_hardcoded_chips -v
```

Output atteso: `FAILED` — `get_fallback_response() takes 0 positional arguments but 1 was given` (o TypeError simile).

---

### Task 2: Backend — implementare `get_fallback_response(message)`

**Files:**
- Modify: `backend/ai/agent.py:147-176` (funzione `get_fallback_response`) e riga 226 (chiamata in `run_agent`)

- [ ] **Step 3: Sostituire `get_fallback_response` in `agent.py`**

Sostituire l'intera funzione `get_fallback_response` (righe 147-176) con:

```python
async def get_fallback_response(message: str = "") -> dict:
    """Risposta demo durante cooldown Gemini. Sceglie il percorso in base al messaggio."""
    msg_lower = message.lower()
    is_muse = "muse" in msg_lower or "museo delle scienze" in msg_lower

    if is_muse:
        origin = KNOWN_PLACES["stazione fs"]
        destination = KNOWN_PLACES["muse"]
        profile = "foot-walking"
        origin_label = "Stazione FS Trento"
        destination_label = "MUSE – Museo delle Scienze"
        reply = (
            "Ecco un percorso a piedi di esempio: Stazione FS Trento → MUSE.\n\n"
            "1. Esci dalla Stazione Ferroviaria di Trento e dirigiti verso sud su Via Dogana.\n"
            "2. Prosegui lungo Viale Verona.\n"
            "3. Svolta a destra su Via Luigi Negrelli.\n"
            "4. Arrivi al MUSE – Museo delle Scienze di Trento.\n\n"
            "⚠️ Il servizio AI è temporaneamente in pausa (quota esaurita). "
            "Questa è una risposta di esempio — riprova tra qualche minuto."
        )
        hardcoded_distance_m = 2000
        hardcoded_duration_s = 1500
    else:
        origin = KNOWN_PLACES["stazione rovereto"]
        destination = KNOWN_PLACES["mart"]
        profile = "cycling-regular"
        origin_label = "Stazione FS Rovereto"
        destination_label = "MART"
        reply = (
            "Ecco un percorso ciclabile di esempio: Stazione FS Rovereto → MART.\n\n"
            "1. Parti dalla Stazione Ferroviaria di Rovereto in bici.\n"
            "2. Imbocca Corso Rosmini verso il centro.\n"
            "3. Svolta su Corso Bettini.\n"
            "4. Arrivi al MART – Museo di Arte Moderna e Contemporanea di Rovereto.\n\n"
            "⚠️ Il servizio AI è temporaneamente in pausa (quota esaurita). "
            "Questa è una risposta di esempio — riprova tra qualche minuto."
        )
        hardcoded_distance_m = 1200
        hardcoded_duration_s = 360

    markers = [
        {"lat": origin[0],      "lon": origin[1],      "type": "origin",      "label": origin_label,      "distance_m": None},
        {"lat": destination[0], "lon": destination[1], "type": "destination", "label": destination_label, "distance_m": None},
    ]

    try:
        route_data = await get_route(origin, destination, profile)
        return {
            "reply":       reply,
            "markers":     markers,
            "route":       route_data["geojson"],
            "chips":       build_chips(route_data["distance_m"], route_data["duration_s"], profile),
            "is_fallback": True,
        }
    except Exception:
        return {
            "reply":       reply,
            "markers":     markers,
            "route":       None,
            "chips":       build_chips(hardcoded_distance_m, hardcoded_duration_s, profile),
            "is_fallback": True,
        }
```

- [ ] **Step 4: Aggiornare la chiamata in `run_agent` (riga 226)**

Sostituire:

```python
    except (ResourceExhausted, GoogleAPIError, Exception):
        return await get_fallback_response()
```

con:

```python
    except (ResourceExhausted, GoogleAPIError, Exception):
        return await get_fallback_response(message)
```

- [ ] **Step 5: Eseguire i test per verificare che passino**

```bash
cd /home/fallenangel/projects/CassandraRosmini/backend
pytest tests/test_agent.py -v
```

Output atteso: tutti i test `PASSED`, nessuna regressione.

- [ ] **Step 6: Commit**

```bash
git add backend/ai/agent.py backend/tests/test_agent.py
git commit -m "feat: get_fallback_response routing per messaggio, fallback MUSE Trento"
```

---

### Task 3: Frontend — `useChat.js` propaga `is_fallback`

**Files:**
- Modify: `frontend/src/composables/useChat.js:23-27`

- [ ] **Step 7: Aggiornare il push del messaggio AI in `useChat.js`**

Trovare il blocco `try` in `useChat.js` (riga 23). Sostituire:

```js
      messages.value.push({
        role: 'ai',
        text: data.reply,
        chips: data.chips || [],
      })
```

con:

```js
      messages.value.push({
        role: 'ai',
        text: data.reply,
        chips: data.chips || [],
        is_fallback: data.is_fallback || false,
      })
```

- [ ] **Step 8: Commit**

```bash
git add frontend/src/composables/useChat.js
git commit -m "feat: propaga is_fallback dal response API al messaggio chat"
```

---

### Task 4: Frontend — nuova suggestion e disclaimer in `ChatPanel.vue`

**Files:**
- Modify: `frontend/src/components/ChatPanel.vue`

- [ ] **Step 9: Aggiungere la nuova suggestion all'array (riga 61-65)**

Sostituire:

```js
const suggestions = [
  'Stazione FS → MART in bici',
  'Parcheggi vicino al Duomo',
  'Come raggiungere il MUSE a piedi?',
]
```

con:

```js
const suggestions = [
  'Stazione FS → MART in bici',
  'Parcheggi vicino al Duomo',
  'Come raggiungere il MUSE a piedi?',
  'da FS - Trento a MUSE - Museo delle scienze di Trento',
]
```

- [ ] **Step 10: Aggiungere il disclaimer nel template**

Nel template, trovare il blocco `.bubble` (riga 13-14):

```html
        <div class="bubble">{{ msg.text }}</div>
        <div v-if="msg.chips?.length" class="chips">
```

Sostituire con:

```html
        <div class="bubble">{{ msg.text }}</div>
        <div v-if="msg.is_fallback" class="fallback-notice">
          ⚠️ Risposta di esempio – servizio AI momentaneamente non disponibile
        </div>
        <div v-if="msg.chips?.length" class="chips">
```

- [ ] **Step 11: Aggiungere lo stile `.fallback-notice` nella sezione `<style scoped>`**

Aggiungere dopo la classe `.chip small` (dopo riga 178):

```css
.fallback-notice {
  font-size: 11px;
  color: #b45309;
  margin-top: 4px;
  max-width: 85%;
}
```

- [ ] **Step 12: Commit**

```bash
git add frontend/src/components/ChatPanel.vue
git commit -m "feat: nuova suggestion FS Trento → MUSE e disclaimer fallback AI"
```

---

## Verifica manuale finale

- [ ] Avviare il backend: `cd backend && uvicorn main:app --reload --port 8000`
- [ ] Avviare il frontend: `cd frontend && npm run dev`
- [ ] Cliccare la suggestion "da FS - Trento a MUSE - Museo delle scienze di Trento"
- [ ] Con Gemini disponibile: risposta normale, nessun disclaimer
- [ ] Con Gemini in rate limit (simulabile con API key errata temporanea): risposta hardcodata con testo FS Trento → MUSE, chips a piedi, disclaimer ⚠️
