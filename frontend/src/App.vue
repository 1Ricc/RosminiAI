<template>
  <div class="app-layout">
    <div class="map-full">
      <MapView ref="mapRef" />
    </div>

    <aside class="chat-overlay" :class="{ collapsed }">
      <ChatPanel @result="onResult" />
    </aside>

    <button class="toggle-btn" @click="collapsed = !collapsed" :title="collapsed ? 'Apri chat' : 'Chiudi chat'">
      {{ collapsed ? '›' : '‹' }}
    </button>

    <div class="poi-toolbar">
      <PoiMenu @show="onPoiShow" @hide="onPoiHide" @toggleCycling="onToggleCycling" @toggleZones="onToggleZones" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import MapView from './components/MapView.vue'
import PoiMenu from './components/PoiMenu.vue'

const mapRef = ref(null)
const collapsed = ref(false)

function onResult(data) {
  mapRef.value?.applyResult(data)
}

function onPoiShow(category, items, emoji) {
  mapRef.value?.showPoiLayer(category, items, emoji)
}

function onPoiHide(category) {
  mapRef.value?.clearPoiLayer(category)
}

function onToggleCycling() {
  mapRef.value?.toggleCyclingLayer()
}

function onToggleZones() {
  mapRef.value?.toggleZonesLayer()
}
</script>

<style>
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body, #app {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  overflow: hidden;
}

.app-layout {
  position: relative;
  width: 100vw;
  height: 100vh;
}

/* Mappa: sempre a schermo pieno, sotto tutto */
.map-full {
  position: absolute;
  inset: 0;
  z-index: 1;
}

/* Chat: overlay sovrapposto a sinistra */
.chat-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 415px;
  height: 100%;
  z-index: 100;
  transition: transform 0.3s ease;
}

.chat-overlay.collapsed {
  transform: translateX(-415px);
}

/* Pulsante toggle: fixed così non viene mai clippato */
.toggle-btn {
  position: fixed;
  left: 415px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 200;
  width: 22px;
  height: 48px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-left: none;
  border-radius: 0 8px 8px 0;
  box-shadow: 3px 0 8px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  font-size: 14px;
  color: #334155;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: left 0.3s ease, color 0.15s, background 0.2s;
  padding: 0;
}

.toggle-btn:hover {
  color: #2563eb;
}

.app-layout:has(.collapsed) .toggle-btn {
  left: 0;
  border-left: 1px solid #e2e8f0;
  border-right: none;
  border-radius: 8px 0 0 8px;
}

/* Toolbar POI in basso al centro della mappa */
.poi-toolbar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 150;
}

</style>
