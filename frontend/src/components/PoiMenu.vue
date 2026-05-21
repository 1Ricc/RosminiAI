<template>
  <div class="poi-menu">
    <button
      v-for="cat in categories"
      :key="cat.id"
      :class="['poi-btn', { active: active.has(cat.id), loading: loadingCat === cat.id }]"
      @click="toggle(cat)"
      :title="cat.label"
    >
      <span class="poi-icon">{{ cat.icon }}</span>
      <span class="poi-label">{{ cat.label }}</span>
    </button>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'

const emit = defineEmits(['show', 'hide', 'toggleCycling', 'toggleZones'])

const categories = [
  { id: 'bike_sharing', icon: '🚲', label: 'Bike Sharing', api: true         },
  { id: 'car_sharing',  icon: '🚗', label: 'Car Sharing',  api: true         },
  { id: 'stazioni',     icon: '🚉', label: 'Stazioni',     api: true         },
  { id: 'taxi',         icon: '🚕', label: 'Taxi',         api: true         },
  { id: 'parcheggi',    icon: '🅿️', label: 'Parcheggi',   api: true         },
  { id: 'patti',        icon: '🏛️', label: 'Cultura',     api: true         },
  { id: 'ciclabili',    icon: '🛣️', label: 'Ciclabili',   api: false        },
  { id: 'zone',         icon: '🗺️', label: 'Zone',         api: false        },
]

const active = reactive(new Set())
const loadingCat = ref(null)

async function toggle(cat) {
  if (!cat.api) {
    if (active.has(cat.id)) {
      active.delete(cat.id)
    } else {
      active.add(cat.id)
    }
    if (cat.id === 'ciclabili') emit('toggleCycling')
    if (cat.id === 'zone')      emit('toggleZones')
    return
  }

  if (active.has(cat.id)) {
    active.delete(cat.id)
    emit('hide', cat.id)
    return
  }

  loadingCat.value = cat.id
  try {
    const { data } = await axios.get(`/api/poi/${cat.id}`)
    active.add(cat.id)
    emit('show', cat.id, data.items, cat.icon)
  } catch (e) {
    console.error('Errore caricamento POI:', e)
  } finally {
    loadingCat.value = null
  }
}
</script>

<style scoped>
.poi-menu {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}

.poi-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1.5px solid rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: #334155;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: background 0.15s, transform 0.1s, box-shadow 0.15s;
  white-space: nowrap;
}

.poi-btn:hover {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.poi-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
}

.poi-btn.loading {
  opacity: 0.6;
  cursor: wait;
}

.poi-icon {
  font-size: 14px;
  line-height: 1;
}

.poi-label {
  letter-spacing: 0.01em;
}
</style>
