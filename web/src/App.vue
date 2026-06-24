<script setup lang="ts">
import { reactive, ref } from 'vue'
import ModelPicker from './components/ModelPicker.vue'
import MessageList from './components/MessageList.vue'
import Composer from './components/Composer.vue'
import { streamChat } from './api/openai'
import type { ChatMessage } from './types'

const model = ref<string>('')
const messages = reactive<ChatMessage[]>([])
const streaming = ref(false)
let abortCtrl: AbortController | null = null

function playAudio(base64Audio: string) {
  const audioBytes = Uint8Array.from(atob(base64Audio), c => c.charCodeAt(0))
  const blob = new Blob([audioBytes], { type: 'audio/wav' })
  const url = URL.createObjectURL(blob)
  const audio = new Audio(url)
  audio.play().catch(() => {})
  audio.onended = () => URL.revokeObjectURL(url)
}

async function send(text: string) {
  if (!model.value) return
  messages.push({ role: 'user', content: text })
  // Placeholder bubble whose `.content` we mutate as deltas arrive.
  const assistant: ChatMessage = reactive({ role: 'assistant', content: '' })
  messages.push(assistant)

  // Build the payload from history WITHOUT the placeholder we just pushed —
  // sending an empty assistant message would confuse the backend.
  const payload = messages.slice(0, -1)

  abortCtrl = new AbortController()
  streaming.value = true
  try {
    for await (const event of streamChat(model.value, payload, abortCtrl.signal)) {
      if (event.type === 'text') {
        assistant.content += event.data
      } else if (event.type === 'audio') {
        playAudio(event.data)
      }
    }
  } catch (e: any) {
    if (e?.name !== 'AbortError') {
      const msg = e?.message ?? String(e)
      assistant.content += (assistant.content ? '\n' : '') + `[error: ${msg}]`
    }
  } finally {
    streaming.value = false
    abortCtrl = null
  }
}

function stop() {
  abortCtrl?.abort()
}

function clear() {
  if (streaming.value) return
  messages.length = 0
}
</script>

<template>
  <div class="app">
    <header>
      <ModelPicker v-model="model" />
      <button class="clear" :disabled="streaming || messages.length === 0" @click="clear">
        清空
      </button>
    </header>
    <MessageList :messages="messages" />
    <Composer :streaming="streaming" :disabled="!model" @send="send" @stop="stop" />
  </div>
</template>

<style>
:root {
  color-scheme: light;
}
html, body, #app {
  height: 100%;
  margin: 0;
}
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  background: #f5f5f5;
  color: #1f2937;
}
</style>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 900px;
  margin: 0 auto;
  border-left: 1px solid #e5e7eb;
  border-right: 1px solid #e5e7eb;
}
header {
  display: flex;
  align-items: stretch;
}
header > :first-child {
  flex: 1 1 auto;
}
.clear {
  border: none;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
  color: #6b7280;
  padding: 0 1rem;
  font-size: 0.85rem;
  cursor: pointer;
}
.clear:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.clear:hover:not(:disabled) {
  color: #1f2937;
}
</style>
