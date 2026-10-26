<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  uploading?: boolean
}>()

const emit = defineEmits<{
  upload: [payload: { name: string; file: File }]
}>()

const name = ref('')
const selectedFile = ref<File | null>(null)

const canSubmit = computed(
  () => name.value.trim() !== '' && selectedFile.value !== null && !props.uploading,
)

function onFileChange(event: Event): void {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
}

// The inputs are kept after submitting so the user can retry if the upload
// fails; on success the parent navigates away.
function onSubmit(): void {
  if (!canSubmit.value || !selectedFile.value) return
  emit('upload', { name: name.value.trim(), file: selectedFile.value })
}
</script>

<template>
  <form class="csv-upload" @submit.prevent="onSubmit">
    <label class="csv-upload__label">
      Dataset name
      <input v-model="name" type="text" class="csv-upload__text" />
    </label>
    <label class="csv-upload__label">
      CSV file
      <input
        type="file"
        accept=".csv,text/csv"
        class="csv-upload__input"
        @change="onFileChange"
      />
    </label>
    <button
      type="submit"
      class="csv-upload__button"
      :disabled="!canSubmit"
    >
      {{ props.uploading ? 'Uploading...' : 'Upload' }}
    </button>
  </form>
</template>

<style scoped>
.csv-upload {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.csv-upload__label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.csv-upload__input {
  font-size: 14px;
}

.csv-upload__input::file-selector-button {
  background-color: var(--color-input-background);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 6px 16px;
  margin-right: 12px;
  font: inherit;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.1s;
}

.csv-upload__input::file-selector-button:hover {
  background-color: #e0e7ff;
}

.csv-upload__text {
  padding: 6px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 14px;
}

.csv-upload__button {
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius);
  background: var(--color-accent);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.csv-upload__button:hover:not(:disabled) {
  background: var(--color-accent-dark);
}

.csv-upload__button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
