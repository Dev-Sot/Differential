import { defineConfig } from "vite";
import { resolve } from "path";

// Flask sirve el bundle desde /static/dist — nombres fijos (sin hash) para no
// necesitar un manifest.json intermedio leido desde Jinja en este pase.
export default defineConfig({
  root: resolve(__dirname, "src"),
  base: "/static/dist/",
  build: {
    outDir: resolve(__dirname, "../static/dist"),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "src/main.ts"),
        style: resolve(__dirname, "src/styles/index.css"),
      },
      output: {
        entryFileNames: "[name].js",
        assetFileNames: "[name].[ext]",
      },
    },
  },
});
