<script setup lang="ts">
import { computed, inject, ref, useId } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import { normalizeTime } from "../time";
const props = defineProps<{
  modelValue: string;
  disabled: boolean;
  error: "invalid" | "failed" | "conflict" | null;
}>();
const emit = defineEmits<{ "update:modelValue": [value: string]; apply: [] }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const input = ref<HTMLInputElement>();
const id = `sax-fixed-start-${useId()}`;
const text = computed(() =>
  dashboard?.language.value === "de"
    ? {
        start: "Täglicher Ladestart",
        hint: "Lädt ab dieser Uhrzeit unabhängig vom Ladestart-SOC und Strompreis bis zum maximalen Netzlade-SOC. Die globale Grenze Max SOC gilt weiterhin. Die automatische Netzladung muss eingeschaltet sein.",
        invalid:
          "Bitte eine vollständige Uhrzeit im Format HH:MM eingeben, zum Beispiel 02:00.",
        failed:
          "Die Änderung ist fehlgeschlagen. Dein Entwurf bleibt erhalten.",
        conflict:
          "Die Einstellungen wurden inzwischen geändert. Dein Entwurf bleibt erhalten. Bitte erneut übernehmen.",
      }
    : {
        start: "Daily charging start",
        hint: "Charges from this time regardless of the start SOC and electricity price until the maximum grid charging SOC is reached. The global Max SOC limit still applies. Automatic grid charging must be on.",
        invalid: "Enter a complete time in HH:MM format, for example 02:00.",
        failed: "The change failed. Your draft is preserved.",
        conflict:
          "The settings have changed elsewhere. Your draft is preserved. Please apply it again.",
      },
);
defineExpose({
  value: () => input.value?.value ?? props.modelValue,
  focus: () => input.value?.focus(),
});
</script>
<template>
  <form class="fixed-time-charging-input" @submit.prevent="emit('apply')">
    <label :for="id">{{ text.start }}</label>
    <input
      :id="id"
      ref="input"
      :value="modelValue"
      type="text"
      inputmode="numeric"
      placeholder="02:00"
      autocomplete="off"
      :disabled="disabled"
      :aria-invalid="error === 'invalid'"
      :aria-describedby="`${id}-hint${error ? ` ${id}-error` : ''}`"
      @input="
        emit('update:modelValue', ($event.target as HTMLInputElement).value)
      "
      @change="
        emit(
          'update:modelValue',
          normalizeTime(($event.target as HTMLInputElement).value),
        )
      "
    />
    <p :id="`${id}-hint`" class="electricity-muted">{{ text.hint }}</p>
    <p v-if="error" :id="`${id}-error`" class="electricity-error" role="alert">
      {{ text[error] }}
    </p>
  </form>
</template>
<style>
.fixed-time-charging-input {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}
.fixed-time-charging-input input {
  box-sizing: border-box;
  max-width: 100%;
  width: 12ch;
  min-height: 44px;
  padding: 10px;
  border: 1px solid var(--divider-color, #ddd);
  border-radius: 6px;
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color, #212121);
  font: inherit;
}
.fixed-time-charging-input p {
  margin: 0;
  line-height: 1.6;
}
.fixed-time-charging-input input:focus-visible {
  outline: 3px solid var(--primary-color, #03a9f4);
  outline-offset: 2px;
}
.fixed-time-charging-input input[aria-invalid="true"] {
  border-color: var(--error-color, #b00020);
}
</style>
