// Tipos globales para librerias cargadas por <script> externo (no npm) y
// APIs de navegador no estandarizadas que main.ts usa.

declare const lucide: {
  createIcons: (opts?: { nodes?: Element[] }) => void;
};

interface Window {
  SpeechRecognition: any;
  webkitSpeechRecognition: any;
}
