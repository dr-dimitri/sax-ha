<script setup lang="ts">
import { computed, inject } from "vue";
import { SAX_DASHBOARD_KEY, type SaxDashboard } from "../ha";

const props = defineProps<{
  domain: Parameters<SaxDashboard["entity"]>[0];
  entityKey: string;
}>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const entity = computed(() => dashboard?.entity(props.domain, props.entityKey));
</script>

<template>
  <div v-if="entity" class="entity-value">
    <span class="entity-value__name">{{ entity.name }}</span>
    <span class="entity-value__state">{{ entity.displayValue }}</span>
  </div>
</template>

<style>
.entity-value {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 20px;
  color: var(--primary-text-color, #212121);
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.entity-value__name {
  color: var(--secondary-text-color, #666);
}

.entity-value__state {
  font-weight: 500;
}
</style>
