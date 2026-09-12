import { defineCustomElement } from "vue";
import SavingsPreview from "./SavingsPreview.ce.vue";

customElements.define(
  "sax-savings-preview",
  defineCustomElement(SavingsPreview),
);
