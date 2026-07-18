const fs = require("fs");
const os = require("os");
const http = require("http"); // <-- Agregamos el módulo HTTP nativo

console.log("==================================");
console.log("Container started successfully");
console.log("==================================");

// Guardamos la info inicial para mostrarla también en la web
const initLog = `
Node Version: ${process.version}
Hostname: ${os.hostname()}
Working directory: ${process.cwd()}
`;
console.log(initLog);

// 1. Crear el Servidor Web escuchando en el puerto 3000
const server = http.createServer((req, res) => {
    // Respondemos con texto plano y estado 200 OK
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    
    let responseText = "¡Hola desde Crane con Node.js!\n\n";
    responseText += initLog + "\n";
    responseText += "Archivos encontrados en el contenedor:\n";
    
    // Leemos los archivos en tiempo real cuando alguien entra a la web
    try {
        const files = fs.readdirSync(".");
        files.forEach(file => {
            if (fs.statSync(file).isFile()) {
                responseText += `\n----- ${file} -----\n`;
                try {
                    responseText += fs.readFileSync(file, "utf8") + "\n";
                } catch {
                    responseText += "<binary>\n";
                }
            }
        });
    } catch (err) {
        responseText += `Error leyendo archivos: ${err.message}\n`;
    }
    
    // Enviamos la respuesta al navegador
    res.end(responseText);
});

// 2. Escuchar en el puerto 3000 (IMPORTANTE: usar '0.0.0.0' para que acepte conexiones externas a Docker)
const PORT = 3000;
server.listen(PORT, "0.0.0.0", () => {
    console.log(`\nServidor web escuchando en http://0.0.0.0:${PORT}`);
});

// Mantenemos tu intervalo para los logs internos de Docker
setInterval(() => {
    console.log("Still alive:", new Date().toISOString());
}, 5000);