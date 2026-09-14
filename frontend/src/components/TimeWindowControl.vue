<script setup lang="ts">
import { computed, inject, onBeforeUnmount, ref, useId, watch } from "vue";
import { SAX_DASHBOARD_KEY } from "../ha";
import { normalizeTime, timeSeconds as seconds } from "../time";

const props = defineProps<{ kind: "timed_charge" | "grid_serving" }>();
type Boundary = "start" | "end";
const dashboard = inject(SAX_DASHBOARD_KEY);
const startEntity = computed(() =>
  dashboard?.entity("time", `${props.kind}_start`),
);
const endEntity = computed(() =>
  dashboard?.entity("time", `${props.kind}_end`),
);
const id = `sax-window-${useId()}`;
const language = computed(() => dashboard?.language.value ?? "en");
const text = computed(() =>
  language.value === "de"
    ? {
        start: "Start",
        end: "Ende",
        unit: "Uhr",
        apply: "Übernehmen",
        confirmed: "Bestätigt",
        draft: "Entwurf",
        duration: "Dauer",
        nextDay: "Ende am Folgetag",
        empty: "Leeres Zeitfenster",
        hour: "Std.",
        minute: "Min.",
        second: "Sek.",
        pending: "Änderung wird an Home Assistant gesendet …",
        awaiting: "Übermittelt · Bestätigung durch Home Assistant ausstehend",
        unavailable: "Zeitfenster nicht verfügbar",
        missingValue: "Nicht verfügbar",
        incompatible:
          "Zeitfenster kann derzeit nicht gemeinsam geändert werden.",
        readOnly: "Keine Berechtigung zum Ändern",
        disconnected: "Keine Verbindung zu Home Assistant",
        changed:
          "Zeitfenster durch Home Assistant aktualisiert. Der Entwurf wurde verworfen.",
        invalid:
          "Bitte eine vollständige, gültige Uhrzeit eingeben (z. B. 12:30).",
        timeHint: "Uhrzeiten im 24-Stunden-Format eingeben: 12:30 oder 1230.",
        help: "Marken ziehen oder Uhrzeit eingeben. Pfeiltasten ändern um eine Minute, Bild auf und Bild ab um 15 Minuten. Pos1 und Ende wählen Tagesanfang und Tagesende.",
        startMarker: "Startmarke",
        endMarker: "Endmarke",
        timeline: "Zeitfenster auf einer 24-Stunden-Leiste",
      }
    : {
        start: "Start",
        end: "End",
        unit: "",
        apply: "Apply",
        confirmed: "Confirmed",
        draft: "Draft",
        duration: "Duration",
        nextDay: "Ends the next day",
        empty: "Empty time window",
        hour: "hr",
        minute: "min",
        second: "sec",
        pending: "Sending change to Home Assistant …",
        awaiting: "Sent · awaiting confirmation from Home Assistant",
        unavailable: "Time window unavailable",
        missingValue: "Unavailable",
        incompatible: "This time window cannot currently be changed as a pair.",
        readOnly: "You do not have permission to change this setting",
        disconnected: "Disconnected from Home Assistant",
        changed:
          "Time window updated by Home Assistant. The draft was discarded.",
        invalid: "Enter a complete, valid time (e.g. 12:30).",
        timeHint: "Enter times in 24-hour format: 12:30 or 1230.",
        help: "Drag the markers or enter a time. Arrow keys change by one minute; Page Up and Page Down by 15 minutes. Home and End select the beginning and end of the day.",
        startMarker: "Start marker",
        endMarker: "End marker",
        timeline: "Time window on a 24-hour timeline",
      },
);
const start = ref("");
const end = ref("");
const edited = ref(false);
const rail = ref<HTMLElement>();
const form = ref<HTMLFormElement>();
const invalidBoundary = ref<Boundary | null>(null);
const localPending = ref(false);
const awaiting = ref(false);
const discarded = ref(false);
let revision = 0;
let drag: {
  boundary: Boundary;
  pointerId: number;
  target: HTMLElement;
  moved: boolean;
  originX: number;
  originSeconds: number;
} | null = null;

function clock(value: number): string {
  const pad = (part: number) => String(part).padStart(2, "0");
  return `${pad(Math.floor(value / 3600))}:${pad(Math.floor(value / 60) % 60)}:${pad(value % 60)}`;
}

function display(value: string): string {
  const parsed = seconds(value);
  if (parsed === null) return "—";
  const normalized = clock(parsed);
  return parsed % 60 ? normalized : normalized.slice(0, 5);
}

function minute(value: string): string {
  return seconds(value) === null ? "" : value.slice(0, 5);
}

const confirmedStart = computed(() => startEntity.value?.state?.state ?? "");
const confirmedEnd = computed(() => endEntity.value?.state?.state ?? "");
const available = computed(
  () =>
    !!startEntity.value?.available &&
    !!endEntity.value?.available &&
    seconds(confirmedStart.value) !== null &&
    seconds(confirmedEnd.value) !== null,
);
const compatible = computed(
  () =>
    typeof startEntity.value?.metadata.device_id === "string" &&
    startEntity.value.metadata.device_id.length > 0 &&
    startEntity.value.metadata.device_id ===
      endEntity.value?.metadata.device_id,
);
const confirmedLabel = computed(() => {
  if (available.value)
    return `${display(confirmedStart.value)} – ${display(confirmedEnd.value)}${text.value.unit ? ` ${text.value.unit}` : ""}`;
  const values = [startEntity.value, endEntity.value].map((entity) =>
    entity?.available && seconds(entity.state?.state ?? "") !== null
      ? `${display(entity.state!.state)}${text.value.unit ? ` ${text.value.unit}` : ""}`
      : text.value.missingValue,
  );
  return values.join(" – ");
});
const valid = computed(
  () => seconds(start.value) !== null && seconds(end.value) !== null,
);
const dirty = computed(
  () =>
    edited.value &&
    (seconds(start.value) !== seconds(confirmedStart.value) ||
      seconds(end.value) !== seconds(confirmedEnd.value)),
);
const pending = computed(
  () =>
    localPending.value ||
    !!startEntity.value?.pending ||
    !!endEntity.value?.pending,
);
const blocked = computed(
  () =>
    !dashboard?.ready.value ||
    !dashboard.connected.value ||
    !available.value ||
    !compatible.value ||
    !startEntity.value?.canControl ||
    !endEntity.value?.canControl ||
    pending.value,
);
const error = computed(() => {
  if (invalidBoundary.value) {
    const boundary = boundaries.value.find(
      (item) => item.key === invalidBoundary.value,
    )!;
    return `${boundary.name}: ${text.value.invalid}`;
  }
  return startEntity.value?.error || endEntity.value?.error;
});
const status = computed(() => {
  if (!dashboard?.connected.value) return text.value.disconnected;
  if (!available.value) return text.value.unavailable;
  if (!compatible.value) return text.value.incompatible;
  if (!startEntity.value?.canControl || !endEntity.value?.canControl)
    return text.value.readOnly;
  if (pending.value) return text.value.pending;
  if (awaiting.value) return text.value.awaiting;
  if (discarded.value) return text.value.changed;
  return "";
});
const visibleStart = computed(() =>
  edited.value || !available.value ? start.value : confirmedStart.value,
);
const visibleEnd = computed(() =>
  edited.value || !available.value ? end.value : confirmedEnd.value,
);
const duration = computed(() => {
  const from = seconds(visibleStart.value);
  const to = seconds(visibleEnd.value);
  if (from === null || to === null) return "—";
  const elapsed = (to - from + 86400) % 86400;
  if (!elapsed) return text.value.empty;
  const hours = Math.floor(elapsed / 3600);
  const minutes = Math.floor(elapsed / 60) % 60;
  const remainder = elapsed % 60;
  return [
    hours && `${hours} ${text.value.hour}`,
    minutes && `${minutes} ${text.value.minute}`,
    remainder && `${remainder} ${text.value.second}`,
    to < from && text.value.nextDay,
  ]
    .filter(Boolean)
    .join(" · ");
});
const segments = computed(() => {
  const from = seconds(visibleStart.value);
  const to = seconds(visibleEnd.value);
  if (from === null || to === null || from === to) return [];
  const ranges =
    to > from
      ? [[from, to]]
      : [
          [from, 86400],
          [0, to],
        ];
  return ranges
    .filter(([left, right]) => left !== right)
    .map(([left, right]) => ({
      left: `${left / 864}%`,
      width: `${(right - left) / 864}%`,
    }));
});
const boundaries = computed(() => [
  {
    key: "start" as const,
    value: start.value,
    name: startEntity.value?.name || text.value.start,
    shortName: text.value.start,
    marker: text.value.startMarker,
  },
  {
    key: "end" as const,
    value: end.value,
    name: endEntity.value?.name || text.value.end,
    shortName: text.value.end,
    marker: text.value.endMarker,
  },
]);

function stopDrag(): void {
  const previous = drag;
  drag = null;
  if (previous?.target.hasPointerCapture?.(previous.pointerId))
    previous.target.releasePointerCapture(previous.pointerId);
}

// REQ-VUE-CHARGING: never mix a stale draft with a changed HA boundary.
watch(
  [
    () => startEntity.value?.metadata.entity_id,
    () => endEntity.value?.metadata.entity_id,
    confirmedStart,
    confirmedEnd,
    available,
    compatible,
    () => startEntity.value?.metadata.device_id,
    () => endEntity.value?.metadata.device_id,
    () => props.kind,
  ],
  (_values, previous) => {
    const oldStart = typeof previous?.[2] === "string" ? previous[2] : "";
    const oldEnd = typeof previous?.[3] === "string" ? previous[3] : "";
    const wasDraft =
      edited.value &&
      (seconds(start.value) !== seconds(oldStart) ||
        seconds(end.value) !== seconds(oldEnd));
    const ownConfirmation = pending.value || awaiting.value;
    revision += 1;
    stopDrag();
    localPending.value = false;
    awaiting.value = false;
    edited.value = false;
    invalidBoundary.value = null;
    discarded.value =
      !!previous?.length && wasDraft && !ownConfirmation && available.value;
    start.value = available.value ? minute(confirmedStart.value) : "";
    end.value = available.value ? minute(confirmedEnd.value) : "";
  },
  { immediate: true, flush: "sync" },
);
watch(
  blocked,
  (value) => {
    if (value) stopDrag();
  },
  { flush: "sync" },
);
onBeforeUnmount(stopDrag);

function edit(boundary: Boundary, value: string): void {
  if (blocked.value) return;
  if (boundary === "start") start.value = value;
  else end.value = value;
  if (invalidBoundary.value === boundary) invalidBoundary.value = null;
  edited.value = true;
  awaiting.value = false;
  discarded.value = false;
}

function typeTime(boundary: Boundary, event: Event): void {
  const input = event.target as HTMLInputElement;
  edit(boundary, input.value);
}

function committedTime(value: string): string {
  const normalized = normalizeTime(value);
  return seconds(normalized) === null ? value : minute(normalized);
}

function readVisibleTimes(committed?: Boundary): void {
  const visible = (["start", "end"] as const).map((boundary) => ({
    boundary,
    input: form.value?.querySelector<HTMLInputElement>(`[name="${boundary}"]`),
  }));
  for (const { boundary, input } of visible) {
    if (!input) continue;
    const current = boundary === "start" ? start.value : end.value;
    const value =
      !committed || boundary === committed
        ? committedTime(input.value)
        : input.value;
    if (input.value !== current || value !== current) edit(boundary, value);
    input.value = value;
  }
}

function commitTime(boundary: Boundary): void {
  if (!blocked.value) readVisibleTimes(boundary);
}

function keyboard(boundary: Boundary, event: KeyboardEvent): void {
  if (blocked.value) return;
  const value = seconds(boundary === "start" ? start.value : end.value);
  if (value === null) return;
  const delta: Record<string, number> = {
    ArrowRight: 60,
    ArrowUp: 60,
    ArrowLeft: -60,
    ArrowDown: -60,
    PageUp: 900,
    PageDown: -900,
  };
  if (!(event.key in delta) && event.key !== "Home" && event.key !== "End")
    return;
  event.preventDefault();
  const next =
    event.key === "Home"
      ? 0
      : event.key === "End"
        ? 86340
        : Math.max(
            0,
            Math.min(86340, Math.floor(value / 60) * 60 + delta[event.key]),
          );
  edit(boundary, minute(clock(next)));
}

function movePointer(event: PointerEvent): void {
  if (
    !drag ||
    drag.pointerId !== event.pointerId ||
    blocked.value ||
    !rail.value
  )
    return;
  const bounds = rail.value.getBoundingClientRect();
  if (bounds.width <= 0) return;
  if (!drag.moved && event.clientX === drag.originX) return;
  const minute = Math.max(
    0,
    Math.min(
      1439,
      Math.round(
        drag.originSeconds / 60 +
          ((event.clientX - drag.originX) / bounds.width) * 1440,
      ),
    ),
  );
  drag.moved = true;
  edit(drag.boundary, clock(minute * 60).slice(0, 5));
}

function startDrag(boundary: Boundary, event: PointerEvent): void {
  if (
    blocked.value ||
    !valid.value ||
    event.button !== 0 ||
    event.isPrimary === false
  )
    return;
  const target = event.currentTarget as HTMLElement;
  target.focus();
  drag = {
    boundary,
    pointerId: event.pointerId,
    target,
    moved: false,
    originX: event.clientX,
    originSeconds: seconds(boundary === "start" ? start.value : end.value)!,
  };
  target.setPointerCapture?.(event.pointerId);
  event.preventDefault();
}

function finishDrag(event: PointerEvent): void {
  if (drag?.pointerId !== event.pointerId) return;
  if (drag.moved) movePointer(event);
  stopDrag();
}

async function submit(): Promise<void> {
  if (!dashboard || blocked.value) return;
  // REQ-VUE-CHARGING: browsers may commit visible values without input events.
  readVisibleTimes();
  invalidBoundary.value =
    seconds(start.value) === null
      ? "start"
      : seconds(end.value) === null
        ? "end"
        : null;
  if (invalidBoundary.value) {
    form.value
      ?.querySelector<HTMLInputElement>(`[name="${invalidBoundary.value}"]`)
      ?.focus();
    return;
  }
  if (!dirty.value) return;
  const current = revision;
  localPending.value = true;
  discarded.value = false;
  const success = await dashboard.performTimeWindow(
    props.kind,
    `${start.value}:00`,
    `${end.value}:00`,
  );
  if (current !== revision) return;
  localPending.value = false;
  // REQ-VUE-ENTITY-BINDING: service acknowledgement is not a state update.
  awaiting.value = success && dirty.value;
}
</script>

<template>
  <form
    v-if="startEntity || endEntity"
    ref="form"
    class="time-window-control"
    :aria-busy="pending"
    @submit.prevent="submit"
  >
    <div class="time-window-control__inputs">
      <label
        v-for="boundary in boundaries"
        :key="boundary.key"
        :for="`${id}-${boundary.key}`"
        class="time-window-control__field"
      >
        <span
          >{{ boundary.name
          }}<template v-if="text.unit"> ({{ text.unit }})</template></span
        >
        <input
          :id="`${id}-${boundary.key}`"
          :name="boundary.key"
          type="text"
          inputmode="numeric"
          autocomplete="off"
          placeholder="HH:MM"
          :value="boundary.value"
          :disabled="blocked"
          :aria-invalid="invalidBoundary === boundary.key"
          :aria-describedby="`${id}-time-hint ${id}-confirmed ${id}-status`"
          @input="typeTime(boundary.key, $event)"
          @change="commitTime(boundary.key)"
          @blur="commitTime(boundary.key)"
        />
      </label>
      <button
        class="time-window-control__apply"
        type="submit"
        :disabled="blocked"
      >
        {{ text.apply }}
      </button>
    </div>
    <p :id="`${id}-time-hint`" class="time-window-control__hint">
      {{ text.timeHint }}
    </p>
    <p :id="`${id}-confirmed`" class="time-window-control__confirmed">
      {{ text.confirmed }}: {{ confirmedLabel }}
    </p>
    <div
      class="time-window-control__timeline"
      :aria-label="text.timeline"
      role="group"
    >
      <div
        ref="rail"
        class="time-window-control__rail"
        :class="{ 'time-window-control__rail--draft': dirty }"
      >
        <span
          v-for="(segment, index) in segments"
          :key="index"
          class="time-window-control__segment"
          :style="segment"
        />
      </div>
      <button
        v-for="boundary in boundaries"
        :key="boundary.key"
        type="button"
        role="slider"
        class="time-window-control__handle"
        :class="`time-window-control__handle--${boundary.key}`"
        :style="{ left: `${(seconds(boundary.value) ?? 0) / 864}%` }"
        :disabled="blocked || !valid"
        :aria-label="boundary.marker"
        aria-valuemin="0"
        aria-valuemax="86340"
        :aria-valuenow="seconds(boundary.value) ?? 0"
        :aria-valuetext="`${display(boundary.value)}${text.unit ? ` ${text.unit}` : ''}`"
        :aria-describedby="`${id}-help ${id}-confirmed`"
        aria-orientation="horizontal"
        @keydown="keyboard(boundary.key, $event)"
        @pointerdown="startDrag(boundary.key, $event)"
        @pointermove="movePointer"
        @pointerup="finishDrag"
        @pointercancel="stopDrag"
        @lostpointercapture="stopDrag"
      >
        <span class="time-window-control__marker-label" aria-hidden="true">{{
          boundary.shortName
        }}</span
        ><span class="time-window-control__marker-dot" aria-hidden="true" />
      </button>
    </div>
    <div class="time-window-control__ticks" aria-hidden="true">
      <span>00</span><span>06</span><span>12</span><span>18</span
      ><span>24</span>
    </div>
    <p class="time-window-control__duration">
      <span>{{ dirty ? text.draft : text.duration }}:</span> {{ duration }}
    </p>
    <p :id="`${id}-help`" class="time-window-control__sr-only">
      {{ text.help }}
    </p>
    <div :id="`${id}-status`" class="time-window-control__feedback">
      <p v-if="error" class="time-window-control__error" role="alert">
        {{ error }}
      </p>
      <p v-else-if="status" role="status">{{ status }}</p>
    </div>
  </form>
</template>

<style>
.time-window-control {
  min-width: 0;
  color: var(--primary-text-color, #212121);
}
.time-window-control__inputs {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 10px;
}
.time-window-control__field {
  display: grid;
  flex: 1 1 136px;
  gap: 5px;
  min-width: 0;
  font-size: 14px;
}
.time-window-control__field input,
.time-window-control__apply {
  box-sizing: border-box;
  min-width: 0;
  max-width: 100%;
  min-height: 44px;
  padding: 8px 10px;
  border: 1px solid var(--divider-color, #767676);
  border-radius: 6px;
  color: inherit;
  background: var(--card-background-color, #fff);
  font: inherit;
  font-size: 16px;
}
.time-window-control__field input {
  width: 100%;
}
.time-window-control__field input[aria-invalid="true"] {
  border-color: var(--error-color, #db4437);
}
.time-window-control__apply {
  flex: 0 0 auto;
  border-color: var(--primary-color, #03a9f4);
  cursor: pointer;
}
.time-window-control__hint,
.time-window-control__confirmed,
.time-window-control__duration {
  margin: 9px 0 0;
  color: var(--secondary-text-color, #666);
  font-size: 14px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.time-window-control__timeline {
  position: relative;
  height: 94px;
  margin: 6px 22px 0;
}
.time-window-control__rail {
  position: absolute;
  top: 44px;
  left: 0;
  right: 0;
  height: 6px;
  border-radius: 3px;
  background: var(--divider-color, #ddd);
  overflow: hidden;
}
.time-window-control__segment {
  position: absolute;
  height: 100%;
  background: var(--primary-color, #03a9f4);
}
.time-window-control__rail--draft .time-window-control__segment {
  background-image: repeating-linear-gradient(
    135deg,
    transparent 0 5px,
    rgb(255 255 255 / 24%) 5px 8px
  );
}
.time-window-control__handle {
  position: absolute;
  display: block;
  width: 44px;
  height: 44px;
  min-height: 0;
  padding: 0;
  transform: translateX(-50%);
  border: 0;
  border-radius: 6px;
  color: inherit;
  background: transparent;
  font: inherit;
  cursor: ew-resize;
  touch-action: none;
}
.time-window-control__handle--start {
  top: 0;
}
.time-window-control__handle--end {
  top: 50px;
}
.time-window-control__marker-label {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: max-content;
  white-space: nowrap;
  font-size: 12px;
  line-height: 16px;
}
.time-window-control__handle--start .time-window-control__marker-label {
  top: 0;
}
.time-window-control__handle--end .time-window-control__marker-label {
  bottom: 0;
}
.time-window-control__marker-dot {
  position: absolute;
  left: 13px;
  width: 18px;
  height: 18px;
  box-sizing: border-box;
  border: 2px solid var(--primary-color, #03a9f4);
  background: var(--card-background-color, #fff);
  border-radius: 50%;
}
.time-window-control__handle--start .time-window-control__marker-dot {
  bottom: 3px;
}
.time-window-control__handle--end .time-window-control__marker-dot {
  top: 3px;
}
.time-window-control__marker-dot::after {
  position: absolute;
  left: 6px;
  width: 2px;
  height: 6px;
  content: "";
  background: var(--primary-color, #03a9f4);
}
.time-window-control__handle--start .time-window-control__marker-dot::after {
  top: 14px;
}
.time-window-control__handle--end .time-window-control__marker-dot::after {
  bottom: 14px;
}
.time-window-control__ticks {
  position: relative;
  height: 18px;
  margin: 0 22px;
  color: var(--secondary-text-color, #666);
  font-size: 12px;
}
.time-window-control__ticks span {
  position: absolute;
  left: 0;
  white-space: nowrap;
}
.time-window-control__ticks span:nth-child(2) {
  left: 25%;
  transform: translateX(-50%);
}
.time-window-control__ticks span:nth-child(3) {
  left: 50%;
  transform: translateX(-50%);
}
.time-window-control__ticks span:nth-child(4) {
  left: 75%;
  transform: translateX(-50%);
}
.time-window-control__ticks span:last-child {
  left: auto;
  right: 0;
}
.time-window-control :disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.time-window-control input:focus-visible,
.time-window-control button:focus-visible {
  outline: 2px solid var(--primary-color, #03a9f4);
  outline-offset: 2px;
}
.time-window-control__feedback {
  margin-top: 6px;
  color: var(--secondary-text-color, #666);
  font-size: 14px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.time-window-control__feedback:empty {
  display: none;
}
.time-window-control__feedback p {
  margin: 0;
}
.time-window-control__error {
  color: var(--error-color, #b71c1c);
}
.time-window-control__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
  border: 0;
}
</style>
