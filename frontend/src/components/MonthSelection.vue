<script setup lang="ts">
import { computed, inject, ref, useId } from "vue";
import EntityControl from "./EntityControl.vue";
import { SAX_DASHBOARD_KEY } from "../ha";

const props = defineProps<{ entityKeys: readonly string[] }>();
const dashboard = inject(SAX_DASHBOARD_KEY);
const expanded = ref(false);
const id = useId();
const detailsId = `sax-months-${id}`;
const language = computed(() => dashboard?.language.value ?? "en");
const text = computed(() =>
  language.value === "de"
    ? {
        edit: "Ändern",
        close: "Schließen",
        allYear: "Ganzjährig",
        none: "Keine Monate ausgewählt · Ganzjährig inaktiv",
        incomplete: "Auswahl nicht vollständig bekannt",
        unknown: "Status unklar",
        unavailable: "Nicht verfügbar",
        hint: "Monate einzeln auswählen. Jede Änderung wird direkt übernommen.",
        pending: "Änderung wird an Home Assistant gesendet …",
        readOnly: "Keine Berechtigung zum Ändern",
        disconnected: "Keine Verbindung zu Home Assistant",
      }
    : {
        edit: "Edit",
        close: "Close",
        allYear: "All year",
        none: "No months selected · Inactive all year",
        incomplete: "Selection is not fully known",
        unknown: "Status unknown",
        unavailable: "Unavailable",
        hint: "Select months individually. Each change is applied immediately.",
        pending: "Sending change to Home Assistant …",
        readOnly: "You do not have permission to change this setting",
        disconnected: "Disconnected from Home Assistant",
      },
);

const months = computed(() => {
  const formatter = new Intl.DateTimeFormat(language.value, {
    month: "long",
    timeZone: "UTC",
  });
  return Array.from({ length: 12 }, (_, index) => {
    const key = props.entityKeys.find((key) =>
      key.endsWith(`_month_${index + 1}`),
    );
    const entity = key ? dashboard?.entity("switch", key) : null;
    const state = entity?.state?.state;
    const known = Boolean(
      entity?.available && (state === "on" || state === "off"),
    );
    return {
      index,
      key,
      entity,
      name:
        entity?.metadata.name ??
        formatter.format(new Date(Date.UTC(2024, index, 1))),
      known,
      selected: known && state === "on",
    };
  });
});
const quarters = computed(() =>
  Array.from({ length: 4 }, (_, index) => ({
    index,
    name: language.value === "de" ? `${index + 1}. Quartal` : `Q${index + 1}`,
    months: months.value.slice(index * 3, index * 3 + 3),
  })),
);
const selectedCount = computed(
  () => months.value.filter((month) => month.selected).length,
);
const unknownMonths = computed(() =>
  months.value.filter((month) => !month.known),
);
const summary = computed(() => {
  if (selectedCount.value === 12) return text.value.allYear;
  if (!selectedCount.value)
    return unknownMonths.value.length ? text.value.incomplete : text.value.none;

  // REQ-VUE-CHARGING: only adjacent, confirmed selections form a range.
  const ranges: string[] = [];
  let first: (typeof months.value)[number] | undefined;
  let last: (typeof months.value)[number] | undefined;
  function finishRange(): void {
    if (first && last)
      ranges.push(
        first.index === last.index ? first.name : `${first.name}–${last.name}`,
      );
    first = undefined;
    last = undefined;
  }
  for (const month of months.value) {
    if (month.selected) {
      first ??= month;
      last = month;
    } else finishRange();
  }
  finishRange();
  return ranges.join(", ");
});
const count = computed(() => {
  const selected = selectedCount.value;
  const unknown = unknownMonths.value.length;
  if (unknown)
    return language.value === "de"
      ? `${selected} ausgewählt · ${unknown} unklar`
      : `${selected} selected · ${unknown} unknown`;
  return language.value === "de"
    ? `${selected} von 12 Monaten ausgewählt`
    : `${selected} of 12 months selected`;
});
const pending = computed(() =>
  months.value.some((month) => month.entity?.pending),
);
const errors = computed(() =>
  months.value.flatMap((month) =>
    month.entity?.error ? [`${month.name}: ${month.entity.error}`] : [],
  ),
);
const readOnlyMonths = computed(() =>
  months.value.filter(
    (month) => month.known && !month.entity?.metadata.can_control,
  ),
);
</script>

<template>
  <div class="month-selection" :aria-busy="pending">
    <div class="month-selection__header">
      <div
        class="month-selection__overview"
        aria-live="polite"
        aria-atomic="true"
      >
        <p class="month-selection__summary">{{ summary }}</p>
        <p class="month-selection__count">{{ count }}</p>
      </div>
      <button
        type="button"
        class="month-selection__toggle"
        :aria-expanded="expanded"
        :aria-controls="detailsId"
        @click="expanded = !expanded"
      >
        {{ expanded ? text.close : text.edit }}
        <svg
          viewBox="0 0 24 24"
          width="18"
          height="18"
          aria-hidden="true"
          :class="{ 'month-selection__chevron--expanded': expanded }"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>
    </div>
    <div class="month-selection__feedback">
      <template v-if="!expanded">
        <p
          v-for="error in errors"
          :key="error"
          class="month-selection__error"
          role="alert"
        >
          {{ error }}
        </p>
        <p v-if="pending" role="status">{{ text.pending }}</p>
      </template>
      <p v-if="!dashboard?.connected.value" role="status">
        {{ text.disconnected }}
      </p>
      <p v-if="unknownMonths.length" role="status">
        {{ text.unknown }}:
        {{ unknownMonths.map((month) => month.name).join(", ") }}
      </p>
      <p v-if="readOnlyMonths.length" role="status">
        {{ text.readOnly }}:
        {{ readOnlyMonths.map((month) => month.name).join(", ") }}
      </p>
    </div>
    <div v-show="expanded" :id="detailsId" class="month-selection__details">
      <p class="month-selection__hint">{{ text.hint }}</p>
      <div class="month-selection__quarters">
        <fieldset
          v-for="quarter in quarters"
          :key="quarter.index"
          class="month-selection__quarter"
        >
          <legend>{{ quarter.name }}</legend>
          <div class="month-selection__options">
            <template v-for="month in quarter.months" :key="month.index">
              <EntityControl
                v-if="month.entity && month.key"
                domain="switch"
                :entity-key="month.key"
                month-tile
                hide-confirmed-value
              />
              <div v-else class="month-selection__missing">
                <label class="month-selection__missing-target">
                  <span>{{ month.name }}</span>
                  <input
                    type="checkbox"
                    role="switch"
                    disabled
                    :indeterminate="true"
                    :aria-describedby="`${detailsId}-${month.index}-missing`"
                  />
                </label>
                <p :id="`${detailsId}-${month.index}-missing`">
                  {{ text.unavailable }}
                </p>
              </div>
            </template>
          </div>
        </fieldset>
      </div>
    </div>
  </div>
</template>

<style>
.month-selection {
  min-width: 0;
}
.month-selection__header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.month-selection__overview {
  flex: 1 1 180px;
  min-width: 0;
  overflow-wrap: anywhere;
}
.month-selection__summary {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  line-height: 1.5;
}
.month-selection__count,
.month-selection__hint {
  margin: 4px 0 0;
  color: var(--secondary-text-color, #666);
  font-size: 14px;
  line-height: 1.5;
}
.month-selection__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  gap: 8px;
  min-height: 44px;
  padding: 8px 12px;
  border: 1px solid var(--divider-color, #e0e0e0);
  border-radius: 8px;
  background: var(--card-background-color, #fff);
  color: var(--primary-text-color, #212121);
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}
.month-selection__toggle:hover {
  background: var(--secondary-background-color, #f5f5f5);
}
.month-selection__toggle:focus-visible,
.month-selection .entity-control__month-target:has(input:focus-visible) {
  outline: 2px solid var(--primary-color, #03a9f4);
  outline-offset: 2px;
}
.month-selection__toggle svg {
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.month-selection__chevron--expanded {
  transform: rotate(180deg);
}
.month-selection__details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--divider-color, #e0e0e0);
}
.month-selection__hint {
  margin: 0 0 16px;
}
.month-selection__quarters {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
}
.month-selection__quarter {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}
.month-selection__quarter legend {
  margin-bottom: 8px;
  padding: 0;
  color: var(--secondary-text-color, #666);
  font-size: 13px;
  font-weight: 500;
}
.month-selection__options {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.month-selection .entity-control.entity-control--month,
.month-selection__missing {
  display: flex;
  flex-direction: column;
  flex-wrap: nowrap;
  align-items: stretch;
  gap: 0;
  min-width: 0;
  padding: 0;
  border: 1px solid var(--divider-color, #e0e0e0);
  border-radius: 8px;
  background: var(--card-background-color, #fff);
}
.month-selection .entity-control.entity-control--selected {
  border-color: color-mix(
    in srgb,
    var(--primary-color, #03a9f4) 55%,
    var(--divider-color, #e0e0e0)
  );
  background: color-mix(
    in srgb,
    var(--primary-color, #03a9f4) 12%,
    var(--card-background-color, #fff)
  );
}
.month-selection .entity-control__month-target,
.month-selection__missing-target {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column-reverse;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 10px 6px;
  border-radius: 7px;
  cursor: pointer;
}
.month-selection .entity-control__month-target:has(:disabled),
.month-selection__missing-target {
  cursor: not-allowed;
}
.month-selection .entity-control__name,
.month-selection__missing-target span {
  min-width: 0;
  max-width: 100%;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  text-align: center;
  overflow-wrap: anywhere;
}
.month-selection .entity-control input[type="checkbox"],
.month-selection__missing input[type="checkbox"] {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  min-height: 22px;
  margin: 0;
  padding: 0;
  accent-color: var(--primary-color, #03a9f4);
}
.month-selection .entity-control__feedback,
.month-selection__missing p {
  flex: 0 0 auto;
  min-width: 0;
  margin: 0;
  padding: 0 12px 10px;
  font-size: 13px;
  line-height: 1.5;
  overflow-wrap: anywhere;
  color: var(--secondary-text-color, #666);
}
.month-selection__feedback {
  display: grid;
  gap: 8px;
  margin-top: 12px;
  color: var(--secondary-text-color, #666);
  font-size: 14px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.month-selection__feedback:empty {
  display: none;
}
.month-selection__feedback p {
  margin: 0;
}
.month-selection__error {
  color: var(--error-color, #b71c1c);
}
@container sax-content (min-width: 600px) {
  .month-selection__quarters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
