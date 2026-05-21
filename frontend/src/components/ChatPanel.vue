<template>
  <div class="chat-panel">
    <div class="chat-header">
      <span class="logo">🌱 RosminiAI</span>
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
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-right: 1px solid rgba(226, 232, 240, 0.6);
  box-shadow: 4px 0 16px rgba(0, 0, 0, 0.12);
  z-index: 10;
  position: relative;
  overflow: hidden;
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
  background: transparent;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.logo {
  font-weight: 800;
  color: #1e293b;
  font-size: 18px;
  letter-spacing: -0.5px;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.5;
  max-width: 85%;
  white-space: pre-line;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.04);
}

.message.user .bubble {
  background: #16a34a;
  color: #ffffff;
  border-radius: 18px 18px 4px 18px;
}

.message.ai .bubble {
  background: rgba(255, 255, 255, 0.85);
  color: #334155;
  border-radius: 4px 18px 18px 18px;
  border: 1px solid rgba(255, 255, 255, 0.6);
}

.chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.chip {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  color: #15803d;
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
  padding: 8px 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.4);
  background: transparent;
  flex-shrink: 0;
}

.suggestion-btn {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  padding: 6px 12px;
  font-size: 12px;
  color: #334155;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.suggestion-btn:hover {
  background: rgba(255, 255, 255, 0.9);
  border-color: #16a34a;
  color: #16a34a;
}

.input-row {
  display: flex;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.4);
  background: transparent;
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  outline: none;
  font-family: inherit;
  transition: border-color 0.2s, background 0.2s;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.02);
}

.chat-input:focus {
  background: #ffffff;
  border-color: #16a34a;
}

.send-btn {
  background: #16a34a;
  color: white;
  border: none;
  border-radius: 12px;
  width: 42px;
  height: 42px;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.2s, transform 0.1s;
  box-shadow: 0 2px 4px rgba(22, 163, 74, 0.3);
}

.send-btn:hover:not(:disabled) {
  background: #15803d;
  transform: translateY(-1px);
}

.send-btn:disabled {
  background: #94a3b8;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}
</style>
