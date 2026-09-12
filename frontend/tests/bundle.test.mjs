import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { SourceTextModule } from "node:vm";
import { JSDOM } from "jsdom";

test("production module runs independently in a browser context", async () => {
  const source = await readFile(
    new URL(
      "../../custom_components/sax_power/frontend/sax-power-vue.js",
      import.meta.url,
    ),
    "utf8",
  );
  const dom = new JSDOM("<!doctype html><body></body>", {
    url: "http://localhost/sax-power-vue/ersparnis",
    runScripts: "outside-only",
  });

  try {
    const { window } = dom;
    assert.equal(window.process, undefined);
    const module = new SourceTextModule(source, {
      context: dom.getInternalVMContext(),
    });
    await module.link(() => {
      throw new Error("The dashboard bundle must not import external modules");
    });
    await module.evaluate();

    const element = window.document.createElement("sax-power-vue-panel");
    element.hass = { language: "de", states: {} };
    element.panel = { config: { entry_id: "entry-1" } };
    window.document.body.append(element);
    await Promise.resolve();
    await Promise.resolve();

    const root = element.shadowRoot;
    assert.equal(root.querySelector("h1").textContent.trim(), "Ersparnis");
    assert.equal(root.querySelectorAll("nav a").length, 5);
    assert.match(
      root.querySelector("style").textContent,
      /--primary-background-color/,
    );
    root.querySelector('nav a[href="/sax-power-vue/ladeautomatik"]').click();
    await Promise.resolve();
    await Promise.resolve();
    assert.equal(window.location.pathname, "/sax-power-vue/ladeautomatik");
    assert.equal(root.querySelector("h1").textContent.trim(), "Ladeautomatik");

    element.hass = { language: "en", states: {} };
    await Promise.resolve();
    await Promise.resolve();
    assert.equal(
      root.querySelector("h1").textContent.trim(),
      "Scheduled charging",
    );

    element.remove();
    await Promise.resolve();
    await Promise.resolve();
    assert.equal(root.querySelector("nav"), null);
  } finally {
    dom.window.close();
  }
});
