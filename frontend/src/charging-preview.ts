import { defineCustomElement } from "vue";
import ChargingPreview from "./ChargingPreview.ce.vue";

customElements.define(
  "sax-charging-preview",
  defineCustomElement(ChargingPreview),
);
