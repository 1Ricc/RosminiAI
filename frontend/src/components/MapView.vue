<template>
  <div class="map-wrapper">
    <div ref="mapEl" class="map-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useMap } from '../composables/useMap.js'

const mapEl = ref(null)
const { init, applyResult, showPoiLayer, clearPoiLayer, toggleCyclingLayer, toggleZonesLayer } = useMap(mapEl)

onMounted(() => {
  setTimeout(init, 50)
})

defineExpose({ applyResult, showPoiLayer, clearPoiLayer, toggleCyclingLayer, toggleZonesLayer })
</script>

<style scoped>
.map-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.map-container {
  width: 100%;
  height: 100%;
}
</style>

<style>
.leaflet-control-attribution {
  font-size: 9px !important;
  opacity: 0.45;
  background: transparent !important;
  box-shadow: none !important;
}

.leaflet-control-attribution:hover {
  opacity: 0.9;
}
</style>
