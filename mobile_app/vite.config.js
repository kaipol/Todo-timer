import { defineConfig } from 'vite';
import { resolve } from 'path';
import { copyFileSync, mkdirSync, existsSync } from 'fs';

// 复制 JS 文件的插件
function copyJsPlugin() {
    return {
        name: 'copy-js-files',
        closeBundle() {
            const jsFiles = [
                'performance.js',
                'storage.js',
                'webdav.js',
                'timer.js',
                'memo.js',
                'diary.js',
                'app.js'
            ];
            
            const distJsDir = resolve(__dirname, 'dist/js');
            if (!existsSync(distJsDir)) {
                mkdirSync(distJsDir, { recursive: true });
            }
            
            jsFiles.forEach(file => {
                const src = resolve(__dirname, 'js', file);
                const dest = resolve(distJsDir, file);
                if (existsSync(src)) {
                    copyFileSync(src, dest);
                    console.log(`Copied: ${file}`);
                }
            });
        }
    };
}

export default defineConfig({
    root: '.',
    base: './',
    publicDir: false,
    build: {
        outDir: 'dist',
        emptyDirBeforeWrite: true,
        minify: 'esbuild',
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'index.html'),
            },
            output: {
                assetFileNames: (assetInfo) => {
                    if (assetInfo.name.endsWith('.css')) {
                        return 'css/[name][extname]';
                    }
                    return 'assets/[name]-[hash][extname]';
                }
            }
        },
    },
    plugins: [copyJsPlugin()]
});
