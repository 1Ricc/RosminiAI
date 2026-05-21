import { ref } from 'vue'
import axios from 'axios'

export function useChat(onResult) {
  const messages = ref([
    {
      role: 'ai',
      text: 'Ciao! Sono RosminiAI 🌱 Dimmi dove vuoi andare e ti aiuto a muoverti in città in modo sostenibile.',
    },
  ])
  const loading = ref(false)
  const error = ref(null)

  async function sendMessage(text) {
    if (!text.trim() || loading.value) return

    messages.value.push({ role: 'user', text })
    loading.value = true
    error.value = null

    try {
      const { data } = await axios.post('/api/chat', { message: text })
      messages.value.push({
        role: 'ai',
        text: data.reply,
        chips: data.chips || [],
        is_fallback: data.is_fallback || false,
      })
      if (onResult) onResult(data)
    } catch (e) {
      error.value = 'Errore di connessione. Riprova.'
      messages.value.push({
        role: 'ai',
        text: 'Mi dispiace, si è verificato un errore. Riprova tra un momento.',
        chips: [],
      })
    } finally {
      loading.value = false
    }
  }

  return { messages, loading, error, sendMessage }
}
