const fs = require("fs");
const os = require("os");
const http = require("http");

console.log("==================================");
console.log("Container started successfully");
console.log("==================================");

// 1. Crear el Servidor Web
const server = http.createServer((req, res) => {
    // CAMBIO CLAVE: Cambiamos a text/html para que el navegador lo renderice sí o sí
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    
    // Empezamos a armar un HTML básico pero limpio
    let html = `
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Crane App Status</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #f4f7f6; color: #333; }
            h1 { color: #0076ff; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
            .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
            pre { background: #272822; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: "Courier New", Courier, monospace; }
            .file-title { font-weight: bold; margin-top: 15px; color: #555; display: block; }
        </style>
    </head>
    <body>
        <h1>🚀 ¡Hola desde tu contenedor en Crane!</h1>
        
        <div class="card">
            <h3>Información del Entorno:</h3>
            <p><strong>Node Version:</strong> ${process.version}</p>
            <p><strong>Hostname:</strong> ${os.hostname()}</p>
            <p><strong>Working Directory:</strong> ${process.cwd()}</p>
        </div>

        <div class="card">
            <h3>Archivos Detectados (Volúmenes Montados):</h3>
    `;

    // 2. Leer los archivos en tiempo real e incrustarlos en el HTML
    try {
        const files = fs.readdirSync(".");
        files.forEach(file => {
            if (fs.statSync(file).isFile()) {
                html += `<span class="file-title">📄 Archivo: <code>${file}</code></span>`;
                try {
                    const content = fs.readFileSync(file, "utf8");
                    // Escapamos caracteres HTML básicos para que no rompa el diseño si hay código
                    const escapedContent = content
                        .replace(/&/g, "&amp;")
                        .replace(/</g, "&lt;")
                        .replace(/>/g, "&gt;");
                    
                    html += `<pre>${escapedContent}</pre>`;
                } catch (err) {
                    html += `<pre style="color: #f92672;">&lt;No se pudo leer el archivo o es binario&gt;</pre>`;
                }
            }
        });
    } catch (err) {
        html += `<p style="color: red;">Error leyendo el directorio: ${err.message}</p>`;
    }

    html += `
        </div>
    </body>
    </html>
    `;
    
    // Enviamos el HTML completo al navegador
    res.end(html);
});

// 2. Escuchar en el puerto 3000
const PORT = 3000;
server.listen(PORT, "0.0.0.0", () => {
    console.log(`\nServidor web escuchando en http://0.0.0.0:${PORT}`);
});

// Intervalo de logs para el docker logs
setInterval(() => {
    console.log("Still alive:", new Date().toISOString());
}, 5000);