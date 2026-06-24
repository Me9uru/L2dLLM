import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
// During dev we proxy /v1/* to the FastAPI backend so the frontend code can
// stay on relative URLs regardless of how it's deployed later.
export default defineConfig({
    plugins: [vue()],
    server: {
        port: 5173,
        proxy: {
            '/v1': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                // No buffering — SSE chunks must flow through immediately.
            },
        },
    },
});
