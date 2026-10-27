<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  uploading?: boolean
}>()

const emit = defineEmits<{
  upload: [payload: { name: string; file: File }]
}>()

const name = ref('')
// v-file-input's model is typed File | File[] | null; without `multiple` it
// holds a single File (or null once cleared).
const fileModel = ref<File | File[] | null>(null)
const selectedFile = computed(() =>
  Array.isArray(fileModel.value) ? (fileModel.value[0] ?? null) : fileModel.value,
)

const canSubmit = computed(
  () => name.value.trim() !== '' && selectedFile.value !== null && !props.uploading,
)

// The inputs are kept after submitting so the user can retry if the upload
// fails; on success the parent navigates away.
function onSubmit(): void {
  if (!canSubmit.value || !selectedFile.value) return
  emit('upload', { name: name.value.trim(), file: selectedFile.value })
}
</script>

<template>
  <form class="csv-upload" @submit.prevent="onSubmit">
    <!-- Persistent "Required" hints explain why Upload is disabled. -->
    <v-text-field
      v-model="name"
      class="csv-upload__field"
      label="Dataset name"
      hint="Required"
      persistent-hint
      density="compact"
      variant="outlined"
      rounded="lg"
      bg-color="surface"
    />
    <v-file-input
      v-model="fileModel"
      class="csv-upload__field"
      label="CSV file"
      accept=".csv,text/csv"
      hint="Required · at most 1 MB"
      persistent-hint
      prepend-icon=""
      prepend-inner-icon="mdi-paperclip"
      density="compact"
      variant="outlined"
      rounded="lg"
      bg-color="surface"
    />
    <v-btn
      type="submit"
      color="primary"
      :disabled="!canSubmit"
      :loading="props.uploading"
      rounded="lg"
    >
      Upload
    </v-btn>
  </form>
</template>

<style scoped>
.csv-upload {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.csv-upload__field {
  flex: 0 1 280px;
}

/* Vertically centre the button on the inputs, not on inputs + hints. */
.csv-upload .v-btn {
  margin-top: 2px;
}


:deep(.v-field--variant-outlined .v-field__outline) {
  color: var(--color-border);
  --v-field-border-opacity: 1; 
}
:deep(.v-field--variant-outlined:hover .v-field__outline) {
  color: #c4c9d0; 
}
:deep(.v-field--variant-outlined .v-field-label--floating) {
  color: var(--color-text-muted);
}

</style>
