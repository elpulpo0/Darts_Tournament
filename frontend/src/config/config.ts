const env = import.meta.env.VITE_ENV;
const PORT_FRONT: string = import.meta.env.VITE_PORT;
const PORT_BACK: string = import.meta.env.VITE_PORT_BACK;

export const backend_url =
  env === 'dev'
    ? `http://localhost:${PORT_BACK}`
    : `http://77.37.51.76:${PORT_FRONT}`;