<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { marked } from 'marked'
import type { ChatMessage } from '../types'

const props = defineProps<{ messages: ChatMessage[] }>()

const scroller = ref<HTMLDivElement | null>(null)

marked.setOptions({
  breaks: true,
  gfm: true,
})

function renderMarkdown(content: string): string {
  return marked.parse(content) as string
}

// Auto-scroll to bottom whenever messages change. `deep: true` is needed
// because streaming mutates the `.content` field of the last message in place,
// which doesn't trigger a shallow watcher.
watch(
  () => props.messages,
  async () => {
    await nextTick()
    const el = scroller.value
    if (el) el.scrollTop = el.scrollHeight
  },
  { deep: true },
)
</script>

<template>
  <div class="message-list" ref="scroller">
    <div v-if="messages.length === 0" class="empty">说点什么吧…</div>
    <div
      v-for="(m, i) in messages"
      :key="i"
      class="bubble"
      :class="m.role"
    >
      <div class="role">{{ m.role }}</div>
      <div v-if="m.role === 'assistant'" class="content markdown-body" v-html="renderMarkdown(m.content || '…')"></div>
      <div v-else class="content">{{ m.content || '…' }}</div>
    </div>
  </div>
</template>

<style scoped>
.message-list {
  flex: 1 1 auto;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.empty {
  color: #9ca3af;
  text-align: center;
  margin-top: 2rem;
  font-size: 0.9rem;
}
.bubble {
  max-width: 75%;
  padding: 0.6rem 0.9rem;
  border-radius: 10px;
  word-wrap: break-word;
  line-height: 1.5;
}
.bubble.user {
  align-self: flex-end;
  background: #2563eb;
  color: #fff;
  white-space: pre-wrap;
}
.bubble.assistant {
  align-self: flex-start;
  background: #ffffff;
  color: #1f2937;
  border: 1px solid #e5e7eb;
}
.bubble.system {
  align-self: center;
  background: #f3f4f6;
  color: #6b7280;
  font-size: 0.8rem;
  font-style: italic;
  white-space: pre-wrap;
}
.role {
  font-size: 0.7rem;
  opacity: 0.6;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.content {
  font-size: 0.95rem;
}
.markdown-body :deep(p) {
  margin: 0.4em 0;
}
.markdown-body :deep(p:first-child) {
  margin-top: 0;
}
.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}
.markdown-body :deep(code) {
  background: #f3f4f6;
  padding: 0.15em 0.35em;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', monospace;
}
.markdown-body :deep(pre) {
  background: #f3f4f6;
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5em 0;
}
.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.85em;
}
.markdown-body :deep(ul), .markdown-body :deep(ol) {
  padding-left: 1.5em;
  margin: 0.4em 0;
}
.markdown-body :deep(li) {
  margin: 0.2em 0;
}
.markdown-body :deep(blockquote) {
  border-left: 3px solid #d1d5db;
  padding-left: 0.75rem;
  margin: 0.5em 0;
  color: #6b7280;
}
.markdown-body :deep(a) {
  color: #2563eb;
  text-decoration: underline;
}
.markdown-body :deep(strong) {
  font-weight: 600;
}
.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 0.5em 0;
  width: 100%;
}
.markdown-body :deep(th), .markdown-body :deep(td) {
  border: 1px solid #d1d5db;
  padding: 0.4em 0.75em;
  text-align: left;
}
.markdown-body :deep(th) {
  background: #f9fafb;
  font-weight: 600;
}
.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 1em 0;
}
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3),
.markdown-body :deep(h4), .markdown-body :deep(h5), .markdown-body :deep(h6) {
  margin: 0.6em 0 0.3em;
  font-weight: 600;
  line-height: 1.3;
}
.markdown-body :deep(h1) { font-size: 1.3em; }
.markdown-body :deep(h2) { font-size: 1.15em; }
.markdown-body :deep(h3) { font-size: 1.05em; }
</style>
