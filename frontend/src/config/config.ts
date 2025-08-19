const env = import.meta.env.VITE_ENV;
const PORT_BACK: string = import.meta.env.VITE_PORT_BACK;

export const backend_url =
  env === 'dev'
    ? `http://localhost:${PORT_BACK}`
    : `https://api.badarts.fr`;