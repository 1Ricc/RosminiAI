<template>
  <div class="app-layout" :class="{ collapsed }">
    <ChatPanel @result="onResult" />
    <MapView ref="mapRef" />
    <button class="toggle-btn" @click="collapsed = !collapsed" :title="collapsed ? 'Apri chat' : 'Chiudi chat'">
      {{ collapsed ? '›' : '‹' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import MapView from './components/MapView.vue'

const mapRef = ref(null)
const collapsed = ref(false)

function onResult(data) {
  mapRef.value?.applyResult(data)
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
}

.app-layout {
  display: grid;
  grid-template-columns: 415px 1fr;
  height: 100vh;
  overflow: hidden;
  position: relative;
  transition: grid-template-columns 0.3s ease;
}

.app-layout.collapsed {
  grid-template-columns: 0px 1fr;
}

.toggle-btn {
  position: fixed;
  left: 415px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1000;
  width: 22px;
  height: 48px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-left: none;
  border-radius: 0 8px 8px 0;
  box-shadow: 3px 0 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  font-size: 14px;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: left 0.3s ease, color 0.15s;
  padding: 0;
}

.toggle-btn:hover {
  color: #2563eb;
}

.app-layout.collapsed .toggle-btn {
  left: 0px;
  border-left: 1px solid #e2e8f0;
  border-right: none;
  border-radius: 8px 0 0 8px;
}
</style>
