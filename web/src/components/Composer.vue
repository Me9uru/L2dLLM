<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ streaming: boolean; disabled?: boolean }>()
const emit = defineEmits<{
  (e: 'send', text: string): void
  (e: 'stop'): void
}>()

const text = ref('')
// Track IME composition so Enter doesn't fire-send while the user is still
// assembling a Chinese / Japanese / Korean character.
const composing = ref(false)

function trySend() {
  const v = text.value.trim()
  if (!v || props.streaming || props.disabled) return
  emit('send', v)
  text.value = ''
}

function onKeydown(e: KeyboardEvent) {
  if (e.key !== 'Enter') return
  if (e.shiftKey) return // newline
  if (composing.value || e.isComposing) return
  e.preventDefault()
  trySend()
}
</script>

<template>
  <div class="composer">
    <textarea
      v-model="text"
      rows="2"
      :disabled="disabled"
      placeholder="发消息… (Enter 发送 / Shift+Enter 换行)"
      @keydown="onKeydown"
      @compositionstart="composing = true"
      @compositionend="composing = false"
    />
    <button
      v-if="!streaming"
      :disabled="!text.trim() || disabled"
      @click="trySend"
    >
      发送
    </button>
    <button v-else class="stop" @click="emit('stop')">停止</button>
  </div>
</template>

<style scoped>
.composer {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-top: 1px solid #e5e7eb;
  background: #ffffff;
}
textarea {
  flex: 1 1 auto;
  resize: none;
  background: #f9fafb;
  color: #1f2937;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.4;
}
textarea:focus {
  outline: none;
  border-color: #2563eb;
}
button {
  align-self: stretch;
  min-width: 5rem;
  padding: 0 1rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
}
button:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}
button.stop {
  background: #dc2626;
}
</style>
