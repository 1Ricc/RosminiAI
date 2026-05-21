import L from 'leaflet'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const MARKER_COLORS = {
  origin:        '#22c55e',
  destination:   '#ec4899',
  bike_sharing:  '#3b82f6',
  car_sharing:   '#8b5cf6',
  parking:       '#f59e0b',
  train_station: '#64748b',
  taxi:          '#ef4444',
}

const ZONE_COLORS = {
  blu: '#3b82f6', cblu: '#60a5fa', cblu2: '#93c5fd',
  rosso: '#ef4444', crosso: '#f87171', crosso2: '#fca5a5',
  verde: '#22c55e', cverde: '#4ade80', cverde2: '#86efac',
  viola: '#a855f7', giallo1: '#eab308', giallo4: '#facc15',
}

function makeColoredMarker(color) {
  return L.divIcon({
    html: `<div style="
      width:14px;height:14px;
      background:${color};
      border:2.5px solid white;
      border-radius:50%;
      box-shadow:0 1px 4px rgba(0,0,0,.3)
    "></div>`,
    className: '',
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

function makeEmojiMarker(emoji) {
  return L.divIcon({
    html: `<div style="
      width:32px;height:32px;
      background:white;
      border-radius:50%;
      box-shadow:0 2px 8px rgba(0,0,0,0.2);
      display:flex;
      align-items:center;
      justify-content:center;
      font-size:16px;
      line-height:1;
    ">${emoji}</div>`,
    className: '',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  })
}

function getPoiLabel(item) {
  return item.fumetto || item.nome || item.via || item.descrizione || item.indirizzo || ''
}

export function useMap(mapEl) {
  let map = null
  let markersLayer = null
  let routeLayer = null
  let cyclingLayer = null
  let cyclingVisible = false
  let zonesLayer = null
  let zonesVisible = false
  const poiLayers = new Map() // category → LayerGroup

  function init() {
    map = L.map(mapEl.value, { zoomControl: false, attributionControl: true })
      .setView([46.0707, 11.1193], 14)

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '© OpenStreetMap contributors © CARTO',
      maxZoom: 19,
    }).addTo(map)

    markersLayer = L.layerGroup().addTo(map)
    routeLayer   = L.layerGroup().addTo(map)

    loadBackgroundLayers()
  }

  async function loadBackgroundLayers() {
    try {
      const r = await fetch('/static/piste_ciclabili.geojson')
      const geojson = await r.json()
      cyclingLayer = L.geoJSON(geojson, {
        style: { color: '#22c55e', weight: 2.5, opacity: 0.65 },
      })
      // Le ciclabili partono nascoste, il bottone le attiva
      cyclingVisible = false
    } catch (e) {
      console.warn('Piste ciclabili non caricate:', e)
    }

    try {
      const r = await fetch('/static/zone_parcheggio.geojson')
      const geojson = await r.json()
      zonesLayer = L.geoJSON(geojson, {
        style: (feat) => {
          const color = ZONE_COLORS[feat.properties.zona] ?? '#94a3b8'
          return { fillColor: color, fillOpacity: 0.25, color, weight: 1.5 }
        },
        onEachFeature: (feat, layer) => {
          layer.bindPopup(
            `<strong>${feat.properties.descrizione ?? 'Zona parcheggio'}</strong><br>Piano: ${feat.properties.pianopark ?? '-'}`
          )
        },
      })
      // Parte nascosta, il bottone la attiva
      zonesVisible = false
    } catch (e) {
      console.warn('Zone parcheggio non caricate:', e)
    }
  }

  function toggleCyclingLayer() {
    if (!cyclingLayer) return
    if (cyclingVisible) {
      cyclingLayer.remove()
      cyclingVisible = false
    } else {
      cyclingLayer.addTo(map)
      cyclingVisible = true
    }
  }

  function toggleZonesLayer() {
    if (!zonesLayer) return
    if (zonesVisible) {
      zonesLayer.remove()
      zonesVisible = false
    } else {
      zonesLayer.addTo(map)
      zonesVisible = true
    }
  }

  function applyResult(data) {
    markersLayer.clearLayers()
    routeLayer.clearLayers()

    const bounds = []

    for (const m of data.markers || []) {
      const color = MARKER_COLORS[m.type] ?? '#6b7280'
      L.marker([m.lat, m.lon], { icon: makeColoredMarker(color) })
        .bindPopup(`<strong>${m.label}</strong>${m.distance_m ? `<br>${m.distance_m} m` : ''}`)
        .addTo(markersLayer)
      bounds.push([m.lat, m.lon])
    }

    if (data.route?.coordinates?.length > 1) {
      const latlngs = data.route.coordinates.map(([lon, lat]) => [lat, lon])
      L.polyline(latlngs, {
        color: '#2563eb',
        weight: 4,
        opacity: 0.85,
        dashArray: '8, 5',
      }).addTo(routeLayer)
      bounds.push(...latlngs)
    }

    if (bounds.length > 0) {
      map.flyToBounds(L.latLngBounds(bounds), { padding: [40, 40], maxZoom: 16, duration: 1.2 })
    }
  }

  function showPoiLayer(category, items, emoji) {
    if (poiLayers.has(category)) {
      poiLayers.get(category).remove()
      poiLayers.delete(category)
    }

    const layer = L.layerGroup()

    for (const item of items) {
      if (!item.lat || !item.lon) continue
      const label = item.nome_completo || getPoiLabel(item) || category
      const extra = [
        item.descrizione ? `<p style="margin:4px 0 0;font-size:11px;color:#64748b">${item.descrizione}</p>` : '',
        item.citta ? `<p style="margin:2px 0 0;font-size:10px;color:#94a3b8">${item.citta}</p>` : '',
      ].join('')
      L.marker([item.lat, item.lon], { icon: makeEmojiMarker(emoji) })
        .bindPopup(`<strong style="font-size:13px">${label}</strong>${extra}`, { maxWidth: 220 })
        .addTo(layer)
    }

    layer.addTo(map)
    poiLayers.set(category, layer)
  }

  function clearPoiLayer(category) {
    if (poiLayers.has(category)) {
      poiLayers.get(category).remove()
      poiLayers.delete(category)
    }
  }

  return { init, applyResult, showPoiLayer, clearPoiLayer, toggleCyclingLayer, toggleZonesLayer }
}
