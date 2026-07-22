/** @type {import('tailwindcss').Config} */
export default {
  content: ["../templates/**/*.html", "./src/**/*.{ts,js}"],
  // preflight desactivado: el reset/CSS existente ya define su propio sistema de diseño
  // (variables --bg/--em/etc, glassmorphism dark UI). El preflight de Tailwind pisaria
  // esas reglas sin que hubiera forma de verificarlo visualmente en este pase.
  // Tailwind queda disponible como utilidades para componentes nuevos.
  corePlugins: { preflight: false },
  theme: {
    extend: {},
  },
  plugins: [],
};
