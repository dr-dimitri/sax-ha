<script setup lang="ts">
import { computed, ref } from "vue";
import { normalizeComparisonTime } from "../tariff-comparison";

const props = defineProps<{
  id: string;
  label: string;
  error?: string;
  time?: boolean;
}>();
const value = defineModel<string>({ required: true });
const visited = ref(false);
const showError = computed(
  () => props.error && (visited.value || value.value.trim()),
);

function commit(event: Event): void {
  const input = event.currentTarget as HTMLInputElement;
  const committed = props.time
    ? normalizeComparisonTime(input.value)
    : input.value;
  if (input.value !== committed) input.value = committed;
  value.value = committed;
  visited.value = true;
}
</script>

<template>
  <div class="field">
    <label :for="id">{{ label }}</label>
    <input
      :id="id"
      v-model="value"
      :inputmode="time ? 'numeric' : 'decimal'"
      :placeholder="time ? 'HH:MM' : undefined"
      :aria-invalid="showError ? true : undefined"
      :aria-describedby="showError ? `${id}-error` : undefined"
      @change="commit"
      @blur="commit"
    />
    <span v-if="showError" :id="`${id}-error`" class="error">{{ error }}</span>
  </div>
</template>
