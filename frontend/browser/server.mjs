import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const routes = new Map([
  ["/fixture.js", ["./fixture.js", "text/javascript"]],
  [
    "/sax_power/frontend/sax-power-vue.js",
    [
      "../../custom_components/sax_power/frontend/sax-power-vue.js",
      "text/javascript",
    ],
  ],
  [
    "/de.json",
    [
      "../../custom_components/sax_power/translations/de.json",
      "application/json",
    ],
  ],
  [
    "/en.json",
    [
      "../../custom_components/sax_power/translations/en.json",
      "application/json",
    ],
  ],
]);
const port = Number(process.env.SAX_PREVIEW_PORT ?? 5190);
createServer(async (request, response) => {
  const pathname = new URL(request.url, "http://localhost").pathname;
  const route = routes.get(pathname);
  const page =
    pathname === "/" ||
    pathname === "/sax-power" ||
    pathname.startsWith("/sax-power-vue");
  if (!route && !page) {
    response.writeHead(404).end();
    return;
  }
  const [file, type] = route ?? ["./fixture.html", "text/html"];
  try {
    const data = await readFile(fileURLToPath(new URL(file, import.meta.url)));
    response
      .writeHead(200, {
        "Content-Type": `${type}; charset=utf-8`,
        "Cache-Control": "no-store",
      })
      .end(data);
  } catch {
    response.writeHead(500).end("Preview asset unavailable");
  }
}).listen(port, "127.0.0.1", () =>
  process.stdout.write(`Dashboard preview: http://127.0.0.1:${port}\n`),
);
