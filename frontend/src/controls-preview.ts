import { defineCustomElement } from "vue";
import ControlsPreview from "./ControlsPreview.ce.vue";

customElements.define(
  "sax-control-preview",
  defineCustomElement(ControlsPreview),
);
