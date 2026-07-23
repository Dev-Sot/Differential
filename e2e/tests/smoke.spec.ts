import { test, expect } from "@playwright/test";

// El overlay de onboarding (initOnboarding() en main.ts) tapa el resto de la
// pagina hasta que se descarta — simulamos un usuario que ya lo vio para
// poder probar el sidebar/tema sin que el overlay intercepte los clicks.
async function skipOnboarding(page: import("@playwright/test").Page) {
  await page.addInitScript(() => localStorage.setItem("medi-onboarding-done", "1"));
}

// Smoke test de la UI real: no ejercita el pipeline RAG (no depende de que
// index/books.index exista), solo confirma que la pagina, el bundle de
// Vite y los handlers globales expuestos en frontend/src/main.ts cargan y
// responden — la brecha que el reporte de auditoria marcaba como "cero
// tests de la interfaz real".

test("la pagina principal carga con el shell del chat", async ({ page }) => {
  const response = await page.goto("/");
  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle(/MEDI-IA/);
  await expect(page.locator(".sidebar")).toBeVisible();
  await expect(page.locator("#chatZone")).toBeVisible();
  await expect(page.locator("#userInput")).toBeVisible();
  await expect(page.locator("#sendBtn")).toBeVisible();
});

test("el bundle de Vite se sirve y no hay errores de consola al cargar", async ({ page }) => {
  const consoleErrors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  const [cssResponse] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/static/dist/style.css")),
    page.goto("/"),
  ]);
  expect(cssResponse.status()).toBe(200);

  // main.js ya debio cargar para cuando la pagina esta en 'load'
  await page.waitForLoadState("load");
  expect(consoleErrors).toEqual([]);
});

test("el toggle del sidebar (window.toggleSidebar via onclick) funciona", async ({ page }) => {
  await skipOnboarding(page);
  await page.goto("/");
  const sidebar = page.locator(".sidebar");
  await expect(sidebar).toBeVisible();

  // en viewport angosto el sidebar arranca oculto; el boton hamburguesa lo abre
  await page.setViewportSize({ width: 480, height: 800 });
  await page.locator(".hamburger-btn").click();
  await expect(sidebar).toHaveClass(/open/);
});

test("el toggle de tema (window.toggleTheme via onclick) cambia data-theme", async ({ page }) => {
  await skipOnboarding(page);
  await page.goto("/");
  const before = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  await page.locator("#themeToggle").click();
  const after = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
  expect(after).not.toBe(before);
});
