import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vitest/config";

export default defineConfig(({ command }) => ({
  plugins: [vue({ customElement: true })],
  define: {
    ...(command === "build"
      ? { "process.env.NODE_ENV": JSON.stringify("production") }
      : {}),
    __VUE_OPTIONS_API__: false,
    __VUE_PROD_DEVTOOLS__: false,
    __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
  },
  build: {
    target: "es2022",
    license: { fileName: "LICENSES.txt" },
    outDir: "../custom_components/sax_power/frontend",
    emptyOutDir: false,
    lib: {
      entry: fileURLToPath(new URL("./src/panel.ts", import.meta.url)),
      formats: ["es"],
      fileName: () => "sax-power-vue.js",
    },
  },
  test: {
    css: true,
    environment: "jsdom",
    environmentOptions: {
      jsdom: { url: "http://localhost/sax-power-vue" },
    },
    include: ["tests/**/*.test.ts"],
    restoreMocks: true,
  },
}));
