<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span class="logo">⬡ Ask Rovereto</span>
    </div>

    <div class="messages" ref="messagesEl">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <div class="bubble">{{ msg.text }}</div>
        <div v-if="msg.chips?.length" class="chips">
          <span v-for="chip in msg.chips" :key="chip.label" class="chip">
            {{ chip.icon }} <strong>{{ chip.value }}</strong>
            <small>{{ chip.label }}</small>
          </span>
        </div>
      </div>

      <div v-if="loading" class="message ai">
        <div class="bubble typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <div class="suggestions">
      <button
        v-for="s in suggestions"
        :key="s"
        class="suggestion-btn"
        @click="submit(s)"
      >{{ s }}</button>
    </div>

    <div class="input-row">
      <input
        v-model="inputText"
        @keyup.enter="submit()"
        placeholder="Dove vuoi andare?"
        :disabled="loading"
        class="chat-input"
      />
      <button @click="submit()" :disabled="loading || !inputText.trim()" class="send-btn">
        ↑
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useChat } from '../composables/useChat.js'

const emit = defineEmits(['result'])
const inputText = ref('')
const messagesEl = ref(null)

const suggestions = [
  'Stazione FS → MART in bici',
  'Parcheggi vicino al Duomo',
  'Come raggiungere il MUSE a piedi?',
]

const { messages, loading, sendMessage } = useChat((data) => emit('result', data))

async function submit(text) {
  const msg = text ?? inputText.value.trim()
  if (!msg) return
  inputText.value = ''
  await sendMessage(msg)
}

watch(messages, async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}, { deep: true })
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  box-shadow: 4px 0 16px rgba(0, 0, 0, 0.12);
  z-index: 10;
  position: relative;
}

.chat-header {
  padding: 14px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: #ffffff;
  flex-shrink: 0;
}

.logo {
  font-weight: 700;
  color: #2563eb;
  font-size: 15px;
  letter-spacing: 0.3px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.message.user {
  align-items: flex-end;
  display: flex;
  flex-direction: column;
}

.message.ai {
  align-items: flex-start;
  display: flex;
  flex-direction: column;
}

.bubble {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.55;
  max-width: 88%;
  white-space: pre-line;
}

.message.user .bubble {
  background: #dbeafe;
  color: #1e3a5f;
  border-radius: 12px 12px 2px 12px;
}

.message.ai .bubble {
  background: #ffffff;
  color: #374151;
  border: 1px solid #e2e8f0;
  border-left: 3px solid #2563eb;
  border-radius: 2px 12px 12px 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.chip {
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  color: #1d4ed8;
  display: flex;
  align-items: center;
  gap: 4px;
}

.chip small {
  opacity: 0.7;
}

/* Typing indicator */
.typing {
  display: flex;
  gap: 5px;
  align-items: center;
  padding: 14px;
}

.typing span {
  width: 7px;
  height: 7px;
  background: #94a3b8;
  border-radius: 50%;
  animation: bounce 1.2s infinite ease-in-out;
}

.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-6px); }
}

.suggestions {
  padding: 8px 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  border-top: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.suggestion-btn {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 4px 10px;
  font-size: 11px;
  color: #475569;
  cursor: pointer;
  transition: background 0.15s;
}

.suggestion-btn:hover {
  background: #e2e8f0;
}

.input-row {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #e2e8f0;
  background: #ffffff;
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s;
}

.chat-input:focus {
  border-color: #2563eb;
}

.send-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  width: 36px;
  height: 36px;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.15s;
}

.send-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.send-btn:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}
</style>
