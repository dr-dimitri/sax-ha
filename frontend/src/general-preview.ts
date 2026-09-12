import { defineCustomElement } from "vue";
import GeneralPreview from "./GeneralPreview.ce.vue";

customElements.define(
  "sax-general-preview",
  defineCustomElement(GeneralPreview),
);
