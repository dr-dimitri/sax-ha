<script setup lang="ts">
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  provide,
  ref,
  useHost,
  watch,
} from "vue";
import { messages, tabPath, tabs } from "./tabs";
import { SAX_DASHBOARD_KEY, useSaxDashboard } from "./ha";
import GeneralView from "./views/GeneralView.vue";
import TimedChargingView from "./views/TimedChargingView.vue";
import GridServingView from "./views/GridServingView.vue";
import DynamicChargingView from "./views/DynamicChargingView.vue";
import SavingsView from "./views/SavingsView.vue";
import type { HomeAssistant, PanelInfo, PanelRoute } from "./types";

const props = defineProps<{
  hass?: HomeAssistant;
  narrow?: boolean;
  panel?: PanelInfo;
  route?: PanelRoute;
}>();

const host = useHost();
const dashboard = useSaxDashboard(
  () => props.hass,
  () => props.panel?.config?.entry_id,
);
provide(SAX_DASHBOARD_KEY, dashboard);
const language = computed(() =>
  props.hass?.language.toLowerCase().startsWith("de") ? "de" : "en",
);
const text = computed(() => messages[language.value]);
const showSidebarButton = computed(
  () =>
    !props.hass?.kioskMode &&
    (props.narrow || props.hass?.dockedSidebar === "always_hidden"),
);
const basePath = computed(() => `/${props.panel?.url_path || "sax-power-vue"}`);
const path = ref(props.route?.path ?? window.location.pathname);
const exclusiveTariff = computed(() => {
  const timed = dashboard.entity("switch", "timed_charge_enabled");
  const dynamic = dashboard.entity("switch", "price_charge_enabled");
  if (!timed?.available || !dynamic?.available) return undefined;
  if (timed.state?.state === "on" && dynamic.state?.state === "off")
    return "ladeautomatik";
  if (dynamic.state?.state === "on" && timed.state?.state === "off")
    return "dynamisches-laden";
  return undefined;
});
const visibleTabs = computed(() =>
  tabs.filter(
    (tab) =>
      !exclusiveTariff.value ||
      !["ladeautomatik", "dynamisches-laden"].includes(tab.path) ||
      tab.path === exclusiveTariff.value,
  ),
);
const requestedPath = computed(() => tabPath(path.value, basePath.value));
const activePath = computed(() =>
  exclusiveTariff.value &&
  ["ladeautomatik", "dynamisches-laden"].includes(requestedPath.value)
    ? exclusiveTariff.value
    : requestedPath.value,
);
const activeTab = computed(() =>
  tabs.find((tab) => tab.path === activePath.value),
);
const heading = ref<HTMLElement>();

watch(
  () => props.route?.path,
  (value) => {
    if (value !== undefined) path.value = value;
  },
);

watch(
  [requestedPath, activePath],
  ([requested, active]) => {
    if (requested === active) return;
    const target = `${basePath.value}/${active}`;
    path.value = target;
    window.history.replaceState(null, "", target);
    window.dispatchEvent(
      new CustomEvent("location-changed", { detail: { replace: true } }),
    );
    void nextTick(() => heading.value?.focus());
  },
  { immediate: true },
);

function syncLocation(): void {
  path.value = window.location.pathname;
}

onMounted(() => {
  window.addEventListener("popstate", syncLocation);
  window.addEventListener("location-changed", syncLocation);
});

onBeforeUnmount(() => {
  window.removeEventListener("popstate", syncLocation);
  window.removeEventListener("location-changed", syncLocation);
});

function navigate(event: MouseEvent, target: string): void {
  if (
    event.button !== 0 ||
    event.ctrlKey ||
    event.metaKey ||
    event.shiftKey ||
    event.altKey
  ) {
    return;
  }
  event.preventDefault();
  if (window.location.pathname !== target) {
    window.history.pushState(null, "", target);
    window.dispatchEvent(
      new CustomEvent("location-changed", { detail: { replace: false } }),
    );
  }
  syncLocation();
  void nextTick(() => heading.value?.focus());
}

function openSidebar(): void {
  host?.dispatchEvent(
    new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }),
  );
}
</script>

<template>
  <div class="dashboard" :class="{ narrow }" :lang="language">
    <header class="header">
      <button
        v-if="showSidebarButton"
        class="menu-button"
        type="button"
        :aria-label="text.menu"
        @click="openSidebar"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <div class="brand">
        <svg class="brand-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M9 3h6M8 5h8a1 1 0 0 1 1 1v14H7V6a1 1 0 0 1 1-1Z" />
          <path d="m13 8-3 5h4l-3 5" />
        </svg>
        <span>SAX Power</span>
      </div>
    </header>

    <nav class="navigation" :aria-label="text.navigation">
      <a
        v-for="tab in visibleTabs"
        :key="tab.path"
        :href="`${basePath}/${tab.path}`"
        :aria-current="activePath === tab.path ? 'page' : undefined"
        @click="navigate($event, `${basePath}/${tab.path}`)"
      >
        {{ tab[language] }}
      </a>
    </nav>

    <main>
      <p v-if="dashboard.error.value" class="status" role="alert">
        {{ dashboard.error.value }}
      </p>
      <p class="introduction">{{ text.introduction }}</p>

      <section class="section" aria-labelledby="section-heading">
        <h1 id="section-heading" ref="heading" tabindex="-1">
          {{ activeTab?.[language] ?? text.notFound }}
        </h1>
        <p v-if="!hass" class="status" role="status">{{ text.loading }}</p>
        <p v-else-if="!panel?.config?.entry_id" class="status" role="status">
          {{ text.missingEntry }}
        </p>
        <GeneralView v-else-if="activePath === 'allgemein'" />
        <TimedChargingView v-else-if="activePath === 'ladeautomatik'" />
        <GridServingView v-else-if="activePath === 'netzdienliches-laden'" />
        <DynamicChargingView v-else-if="activePath === 'dynamisches-laden'" />
        <SavingsView
          v-else-if="activePath === 'ersparnis'"
          :hass="hass"
          :entry-id="panel?.config?.entry_id"
        />
        <div v-else class="status">
          <p>{{ text.notFoundDescription }}</p>
          <a
            :href="`${basePath}/allgemein`"
            @click="navigate($event, `${basePath}/allgemein`)"
          >
            {{ text.returnToOverview }}
          </a>
        </div>
      </section>
    </main>
  </div>
</template>

<style>
:host {
  display: block;
  height: 100%;
  color: var(--primary-text-color, #212121);
  background: var(--primary-background-color, #fafafa);
  font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
  font-size: 14px;
}

* {
  box-sizing: border-box;
}

.dashboard {
  min-height: 100%;
  container: sax-panel / inline-size;
}

.header {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 64px;
  padding: 8px 24px;
  background: var(--app-header-background-color, var(--primary-color, #03a9f4));
  color: var(--app-header-text-color, #fff);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 500;
}

.header svg {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.brand-icon {
  width: 30px;
  height: 30px;
}

.menu-button {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  margin-left: -10px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.menu-button svg {
  width: 24px;
  height: 24px;
}

.navigation {
  display: flex;
  overflow-x: auto;
  padding: 0 16px;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
  background: var(--card-background-color, #fff);
}

.navigation a {
  display: flex;
  align-items: center;
  min-height: 56px;
  padding: 12px 16px;
  border-bottom: 3px solid transparent;
  color: var(--secondary-text-color, #666);
  text-decoration: none;
  white-space: nowrap;
}

.navigation a[aria-current="page"] {
  border-color: var(--primary-color, #03a9f4);
  color: var(--primary-text-color, #212121);
  font-weight: 600;
}

a {
  color: var(--primary-text-color, #212121);
  text-underline-offset: 3px;
}

a:focus-visible,
button:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: -4px;
}

main {
  max-width: 1120px;
  margin: 0 auto;
  padding: 28px 24px 48px;
}

.introduction {
  margin: 0 0 24px;
  line-height: 1.6;
  color: var(--secondary-text-color, #666);
}

.section {
  container: sax-content / inline-size;
  overflow-wrap: anywhere;
  padding: 28px;
  border: var(--ha-card-border-width, 1px) solid
    var(--ha-card-border-color, var(--divider-color, #e0e0e0));
  border-radius: var(--ha-card-border-radius, 12px);
  background: var(--ha-card-background, var(--card-background-color, #fff));
  box-shadow: var(--ha-card-box-shadow, none);
}

h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  line-height: 1.35;
}

h1:focus {
  outline: none;
}

h2 {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
}

.status {
  margin-top: 24px;
  line-height: 1.7;
}

.narrow .header {
  padding-right: 16px;
  padding-left: 16px;
}

.narrow main {
  padding: 16px 12px 32px;
}

@container sax-panel (min-width: 940px) {
  .header {
    min-height: 56px;
    padding: 6px 20px;
  }

  .navigation a {
    min-height: 48px;
    padding: 8px 14px;
  }

  main {
    max-width: 1360px;
    padding: 16px 20px 20px;
  }

  .introduction {
    margin-bottom: 12px;
  }

  .section {
    padding: 20px;
  }

  h1 {
    font-size: 22px;
  }
}

@media (max-width: 600px) {
  .header {
    gap: 8px;
    padding: 8px 16px;
  }

  .brand {
    gap: 6px;
    font-size: 18px;
  }

  .brand-icon {
    display: none;
  }

  .navigation {
    padding: 0 4px;
  }

  main {
    padding: 16px 12px 32px;
  }

  .introduction {
    margin-bottom: 16px;
  }

  .section {
    padding: 20px;
  }

  h1 {
    font-size: 22px;
  }
}
</style>
