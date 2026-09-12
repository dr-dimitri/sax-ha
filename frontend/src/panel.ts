import { defineCustomElement } from "vue";
import Panel from "./Panel.ce.vue";

export const SaxPowerVuePanel = defineCustomElement(Panel);

if (!customElements.get("sax-power-vue-panel")) {
  customElements.define("sax-power-vue-panel", SaxPowerVuePanel);
}
