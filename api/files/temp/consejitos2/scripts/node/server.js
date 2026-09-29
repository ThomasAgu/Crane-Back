const http = require('http');
const fs = require('fs');
const mariadb = require('mariadb');

// Configuración del pool usando las variables de entorno de Docker
const pool = mariadb.createPool({
     host: process.env.DB_HOST,
     user: process.env.DB_USER,
     password: process.env.DB_PASSWORD,
     database: process.env.DB_NAME,
     connectionLimit: 5
});

// Inicializar la tabla si no existe
async function initDB() {
    let conn;
    try {
        conn = await pool.getConnection();
        await conn.query(`
            CREATE TABLE IF NOT EXISTS consejos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                consejo TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);
        console.log('Tabla de consejos verificada/creada con éxito.');
    } catch (err) {
        console.error('Error inicializando base de datos:', err);
    } finally {
        if (conn) conn.end();
    }
}

initDB();

const server = http.createServer(async (req, res) => {
    // 1. API: Obtener todos los consejos (GET /api/consejos)
    if (req.url === '/api/consejos' && req.method === 'GET') {
        let conn;
        try {
            conn = await pool.getConnection();
            const rows = await conn.query('SELECT nombre, consejo FROM consejos ORDER BY fecha DESC');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(rows));
        } catch (err) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: err.message }));
        } finally {
            if (conn) conn.end();
        }
    }
    // 2. API: Guardar un nuevo consejo (POST /api/consejos)
    else if (req.url === '/api/consejos' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', async () => {
            let conn;
            try {
                const { nombre, consejo } = JSON.parse(body);
                if (!nombre || !consejo) throw new Error('Campos incompletos');
                
                conn = await pool.getConnection();
                await conn.query('INSERT INTO consejos (nombre, consejo) VALUES (?, ?)', [nombre, consejo]);
                
                res.writeHead(201, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ success: true }));
            } catch (err) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: err.message }));
            } finally {
                if (conn) conn.end();
            }
        });
    }
    // 3. Frontend: Servir el HTML con el Formulario (Cualquier otra ruta)
    else {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>El Club del Consejo</title>
                <style>
                    body { font-family: sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; background: #f9f9f9; }
                    .form-group { margin-bottom: 15px; }\n                    label { display: block; margin-bottom: 5px; font-weight: bold; }
                    input[type="text"], textarea { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
                    button { background: #0076ff; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
                    button:hover { background: #0056b3; }
                    .consejo-card { background: white; padding: 15px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 15px; }
                    .autor { font-weight: bold; color: #555; font-size: 0.9em; margin-top: 5px; text-align: right; }
                </style>
            </head>
            <body>
                <h1>🏛️ El Club del Consejo</h1>
                
                <div style="background: white; padding: 20px; border-radius: 6px; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                    <div class="form-group">
                        <label>Tu Nombre:</label>
                        <input type=\"text\" id="nombre" placeholder="Ej: Marco Aurelio">
                    </div>
                    <div class="form-group">
                        <label>Tu Consejo:</label>
                        <textarea id="consejo" rows="3" placeholder="Ej: No gastes más tiempo argumentando acerca de lo que debe ser un buen hombre. Sé uno."></textarea>
                    </div>
                    <button onclick="enviarConsejo()">Enviar Consejo</button>
                </div>

                <h2>📜 Consejos Recientes</h2>
                <div id="lista-consejos">Cargando sabiduría...</div>

                <script>
                    async function cargarConsejos() {
                        try {
                            const res = await fetch('/api/consejos');
                            const consejos = await res.json();
                            const lista = document.getElementById('lista-consejos');
                            if(consejos.length === 0) {
                                lista.innerHTML = '<p>No hay consejos aún. ¡Sé el primero!</p>';
                                return;
                            }
                            lista.innerHTML = consejos.map(c => \`
                                <div class="consejo-card">
                                    <div class="texto">“\${c.consejo}”</div>
                                    <div class="autor">— \${c.nombre}</div>
                                </div>
                            \`).join('');
                        } catch(err) {
                            document.getElementById('lista-consejos').innerHTML = '<p>Error cargando consejos.</p>';
                        }
                    }

                    async function enviarConsejo() {
                        const nombre = document.getElementById('nombre').value;
                        const consejo = document.getElementById('consejo').value;
                        
                        if(!nombre || !consejo) return alert('Por favor, completa ambos campos');

                        await fetch('/api/consejos', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ nombre, consejo })
                        });

                        document.getElementById('nombre').value = '';
                        document.getElementById('consejo').value = '';
                        cargarConsejos();
                    }

                    cargarConsejos();
                </script>
            </body>
            </html>
        `);
    }
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, '0.0.0.0', () => {
    console.log(`Servidor corriendo en el puerto ${PORT}`);
});