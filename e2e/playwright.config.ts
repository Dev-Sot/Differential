import { defineConfig } from "@playwright/test";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");
const isWindows = process.platform === "win32";
const pythonBin = isWindows
  ? path.join(repoRoot, "venv", "Scripts", "python.exe")
  : path.join(repoRoot, "venv", "bin", "python");

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: "http://127.0.0.1:5000",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `${pythonBin} app.py`,
    cwd: repoRoot,
    url: "http://127.0.0.1:5000/",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
