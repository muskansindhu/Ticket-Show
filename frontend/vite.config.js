import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/shows": "http://localhost:8000",
      "/venues": "http://localhost:8000",
      "/screens": "http://localhost:8000",
      "/schedules": "http://localhost:8000",
      "/bookings": "http://localhost:8000",
      "/payments": "http://localhost:8000"
    }
  }
});
