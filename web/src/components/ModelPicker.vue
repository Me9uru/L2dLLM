<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { listModels } from '../api/openai'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

const models = ref<string[]>([])
const error = ref<string>('')

onMounted(async () => {
  try {
    models.value = await listModels()
    // If nothing was selected yet and we got at least one model, pick the
    // first one (prefer "default" if present).
    if (!props.modelValue && models.value.length > 0) {
      const preferred = models.value.includes('default') ? 'default' : models.value[0]
      emit('update:modelValue', preferred)
    }
  } catch (e) {
    error.value = String(e)
  }
})



function onChange(e: Event) {
  emit('update:modelValue', (e.target as HTMLSelectElement).value)
}

// If the chosen value disappears from the list (shouldn't happen mid-session),
// fall back to the first available one to avoid showing an empty select.
watch(
  () => models.value,
  (list) => {
    if (list.length > 0 && !list.includes(props.modelValue)) {
      emit('update:modelValue', list[0])
    }
  },
)
</script>

<template>
  <div class="model-picker">
    <label>Model</label>
    <select :value="modelValue" @change="onChange" :disabled="models.length === 0">
      <option v-if="models.length === 0" value="">(loading…)</option>
      <option v-for="m in models" :key="m" :value="m">{{ m }}</option>
    </select>
    <span v-if="error" class="err">{{ error }}</span>
  </div>
</template>

<style scoped>
.model-picker {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
}
label {
  font-size: 0.85rem;
  color: #6b7280;
}
select {
  background: #ffffff;
  color: #1f2937;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  padding: 0.25rem 0.5rem;
  font-size: 0.9rem;
}
.err {
  color: #dc2626;
  font-size: 0.8rem;
  margin-left: 0.5rem;
}
</style>
