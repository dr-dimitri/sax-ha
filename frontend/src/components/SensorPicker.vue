<script setup lang="ts">
import { computed } from "vue";
import type { HomeAssistant } from "../types";
const props = defineProps<{
  hass?: HomeAssistant;
  modelValue: string | null;
  label: string;
  disabled?: boolean;
  name?: string;
  invalid?: boolean;
  describedBy?: string;
}>();
const emit = defineEmits<{ "update:modelValue": [value: string | null] }>();
const choices = computed(() => {
  const result = Object.values(props.hass?.states ?? {})
    .filter((state) => state.entity_id.startsWith("sensor."))
    .map((state) => ({
      id: state.entity_id,
      name:
        typeof state.attributes.friendly_name === "string"
          ? state.attributes.friendly_name
          : state.entity_id,
    }));
  if (
    props.modelValue &&
    !result.some((choice) => choice.id === props.modelValue)
  )
    result.push({ id: props.modelValue, name: props.modelValue });
  return result.sort((a, b) => a.name.localeCompare(b.name));
});
</script>
<template>
  <label class="sensor-picker"
    >{{ label
    }}<select
      :value="modelValue ?? ''"
      :disabled="disabled"
      :name="name"
      :aria-invalid="invalid || undefined"
      :aria-describedby="describedBy"
      @change="
        emit(
          'update:modelValue',
          ($event.target as HTMLSelectElement).value || null,
        )
      "
    >
      <option value="">
        {{
          hass?.language?.startsWith("de")
            ? "Nicht konfiguriert"
            : "Not configured"
        }}
      </option>
      <option v-for="choice in choices" :key="choice.id" :value="choice.id">
        {{ choice.name }}
      </option>
    </select></label
  >
</template>
<style>
.sensor-picker {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  font-size: 14px;
}
.sensor-picker select {
  max-width: 100%;
  width: 100%;
  min-width: 0;
  min-height: 44px;
  padding: 10px;
  font: inherit;
  color: var(--primary-text-color, #222);
  background: var(--card-background-color, #fff);
  border: 1px solid var(--divider-color, #ccc);
  border-radius: 6px;
}
</style>
