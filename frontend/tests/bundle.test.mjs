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
      [...root.querySelectorAll("style")]
        .map((style) => style.textContent)
        .join("\n"),
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

    const calls = [];
    const unsubscribe = () => {};
    element.hass = {
      language: "de",
      connection: {
        connected: true,
        subscribeMessage: async (callback) => {
          callback({
            entities: [
              {
                entity_id: "sensor.renamed_soc",
                domain: "sensor",
                key: "soc",
                name: "Ladezustand",
                states: {},
                can_control: false,
              },
              {
                entity_id: "number.renamed_limit",
                domain: "number",
                key: "max_soc",
                name: "Maximaler Ladezustand",
                states: {},
                can_control: true,
              },
            ],
          });
          return unsubscribe;
        },
        addEventListener: () => {},
        removeEventListener: () => {},
      },
      states: {
        "sensor.renamed_soc": {
          entity_id: "sensor.renamed_soc",
          state: "63.5",
          attributes: { unit_of_measurement: "%" },
        },
        "number.renamed_limit": {
          entity_id: "number.renamed_limit",
          state: "80",
          attributes: { min: 10, max: 100, step: 1, unit_of_measurement: "%" },
        },
      },
      callService: async (...args) => calls.push(args),
    };
    root.querySelector('nav a[href="/sax-power-vue/allgemein"]').click();
    await Promise.resolve();
    await Promise.resolve();
    assert.equal(root.querySelector(".placeholder"), null);
    assert.match(root.textContent, /Ladezustand/);
    assert.match(root.textContent, /63,5 %/);
    const styles = [...root.querySelectorAll("style")]
      .map((style) => style.textContent)
      .join("\n");
    for (const selector of [
      ".entity-gauge__segment",
      ".general-view__rows",
      ".entity-control__input",
    ]) {
      assert.ok(
        styles.includes(selector),
        `Missing bundled style: ${selector}`,
      );
    }
    assert.equal(calls.length, 0);
    const input = root.querySelector('input[type="number"]');
    assert.ok(
      input,
      "The production bundle includes the shared number control",
    );
    input.value = "85";
    input.dispatchEvent(new window.Event("input", { bubbles: true }));
    input.form.dispatchEvent(
      new window.Event("submit", { bubbles: true, cancelable: true }),
    );
    await Promise.resolve();
    await Promise.resolve();
    assert.equal(calls.length, 1);
    assert.equal(calls[0][0], "number");
    assert.equal(calls[0][1], "set_value");
    assert.equal(calls[0][2].value, 85);
    assert.equal(calls[0][3].entity_id, "number.renamed_limit");
    assert.match(
      root.querySelector(".entity-control__value").textContent,
      /80 %/,
    );

    element.remove();
    await Promise.resolve();
    await Promise.resolve();
    assert.equal(root.querySelector("nav"), null);
  } finally {
    dom.window.close();
  }
});
