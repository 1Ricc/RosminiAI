# Design: Suggested Query FS Trento → MUSE con Fallback Gemini

**Data:** 2026-05-21  
**Branch:** dev/frontend  
**Scope:** Aggiunta di una query suggerita "da FS - Trento a MUSE" con risposta hardcodata quando Gemini è in rate limit.

---

## Contesto

Il frontend espone tre suggerimenti cliccabili in `ChatPanel.vue`. Quando l'utente clicca un suggerimento, la stringa viene inviata al backend tramite `POST /api/chat`. Il backend esegue il loop Gemini function-calling; se Gemini restituisce `ResourceExhausted` (rate limit), chiama `get_fallback_response()` che attualmente restituisce sempre il percorso FS Rovereto → MART in bici — errato per query su Trento.

---

## Obiettivo

1. Aggiungere il suggerimento **"da FS - Trento a MUSE - Museo delle scienze di Trento"** all'interfaccia.
2. Quando Gemini è in rate limit e l'utente ha chiesto di quel percorso, il backend restituisce una risposta completa e corretta (testo + chips + markers) per FS Trento → MUSE a piedi.
3. Il frontend mostra un disclaimer testuale nella bubble AI per indicare che si tratta di una risposta di esempio.

---

## Architettura

### Backend — `backend/ai/agent.py`

**Modifica `get_fallback_response`:**

```python
async def get_fallback_response(message: str = "") -> dict:
```

La funzione accetta il testo originale della query. Seleziona il percorso di fallback in base al contenuto del messaggio:

| Condizione (case-insensitive) | Percorso fallback | Profilo |
|---|---|---|
| `"muse"` o `"museo delle scienze"` nel messaggio | Stazione FS Trento → MUSE | `foot-walking` |
| altrimenti | Stazione FS Rovereto → MART | `cycling-regular` |

Le coordinate vengono lette da `KNOWN_PLACES` già presente:
- `"stazione fs"` → `(46.0707, 11.1193)`
- `"muse"` → `(46.0613, 11.1164)`

La funzione tenta la chiamata ORS per ottenere route reale e chips calcolate. Se ORS fallisce, usa chips hardcoded:
- Trento FS → MUSE: `~2.0 km`, `~25 min`, CO₂ calcolata via `co2_saved_grams()`

Tutte le risposte di fallback includono `"is_fallback": True` nel dict restituito.

Il testo della risposta per il percorso Trento:
```
Ecco un percorso a piedi di esempio: Stazione FS Trento → MUSE.

1. Esci dalla Stazione Ferroviaria di Trento e dirigiti verso sud su Via Dogana.
2. Prosegui lungo Viale Verona.
3. Svolta a destra su Via Luigi Negrelli.
4. Arrivi al MUSE – Museo delle Scienze di Trento.

⚠️ Il servizio AI è temporaneamente in pausa (quota esaurita).
Questa è una risposta di esempio — riprova tra qualche minuto.
```

**Modifica chiamante in `run_agent`:**

```python
except (ResourceExhausted, GoogleAPIError, Exception):
    return await get_fallback_response(message)
```

### Frontend — `frontend/src/components/ChatPanel.vue`

**Array `suggestions`:** aggiunge il nuovo elemento:

```js
const suggestions = [
  'Stazione FS → MART in bici',
  'Parcheggi vicino al Duomo',
  'Come raggiungere il MUSE a piedi?',
  'da FS - Trento a MUSE - Museo delle scienze di Trento',
]
```

**Rendering del disclaimer:** il composable `useChat` già riceve `data` dalla risposta. Quando `data.is_fallback === true`, aggiunge una proprietà `is_fallback: true` al messaggio inserito in `messages`. Il template in `ChatPanel.vue` mostra sotto la bubble un testo secondario:

```html
<div v-if="msg.is_fallback" class="fallback-notice">
  ⚠️ Risposta di esempio – servizio AI momentaneamente non disponibile
</div>
```

Stile `.fallback-notice`: testo piccolo (`font-size: 11px`), colore ambra (`#b45309`), margine sopra di 4px.

### Frontend — `frontend/src/composables/useChat.js`

Nel blocco `try`, propagare `is_fallback` dal response al messaggio:

```js
messages.value.push({
  role: 'ai',
  text: data.reply,
  chips: data.chips || [],
  is_fallback: data.is_fallback || false,
})
```

---

## Flusso dati

```
[Utente clicca suggestion]
        ↓
ChatPanel.vue: submit("da FS - Trento a MUSE...")
        ↓
useChat.js: POST /api/chat { message }
        ↓
backend run_agent(message)
    ├─ [Gemini OK] → risposta normale, is_fallback: false (assente)
    └─ [ResourceExhausted] → get_fallback_response(message)
            ├─ message contiene "muse" → fallback Trento FS → MUSE
            └─ altrimenti → fallback Rovereto FS → MART
        ↓
response: { reply, chips, markers, route, is_fallback: true }
        ↓
useChat.js: push messaggio con is_fallback: true
        ↓
ChatPanel.vue: bubble normale + disclaimer ⚠️
```

---

## Dati hardcoded (fallback ORS non disponibile)

| Campo | Valore |
|---|---|
| Distanza | 2000 m (2.0 km) |
| Durata | 1500 s (25 min) |
| Profilo | `foot-walking` |
| CO₂ | calcolata via `co2_saved_grams(2000, "foot-walking")` |

---

## Scope escluso

- Nessuna modifica alla logica Gemini o al loop di function calling.
- Nessun nuovo endpoint API.
- Nessun test aggiuntivo (la funzione `get_fallback_response` è già testata implicitamente dal test di errore Gemini esistente).
