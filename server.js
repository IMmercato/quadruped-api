import express from "express";
import dotenv from "dotenv";
import http from "http";
import path from "path";
import { execFile } from "child_process";
import { WebSocketServer } from "ws";
import { fileURLToPath } from "url";
import { dirname } from "path";
import { error, timeStamp } from "console";
import { stderr, stdout } from "process";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Generate API keys and save them on .env with: node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
const VALID_API_KEYS = new Set(process.env.ALLOWED_KEYS ? process.env.ALLOWED_KEYS.split(',') : []);
// Whitelist specific IPs
const WHITELISTED_IPS = new Set([]);    // Now allowing all IPs
// Rate limiting config
const RATE_LIMIT_WINDOW = 60000;    // 1 minute
const RATE_LIMIT_MAX_REQUESTS = 100;
const rateLimitMap = new Map();

// API Key Authentication
function authAPIKey(req, res, next) {
    const apiKey = req.headers['x-api-key'] || req.query.apiKey;

    if (!apiKey) {
        return res.status(401).json({
            error: "Authentication required",
            message: "Please provide an API key in X-API-Key header or apiKey query parameter"
        });
    }

    if (!VALID_API_KEYS.has(apiKey)) {
        return res.status(403).json({
            error: "Invalid API key",
            message: "The provided API key is not authorized"
        });
    }

    next();
}

// IP Whitelist
function checkIP(req, res, next) {
    if (WHITELISTED_IPS.size === 0) {
        return next();  // Skip if empty
    }

    const clientIP = req.ip || req.connection.remoteAddress;

    if (!WHITELISTED_IPS.has(clientIP)) {
        console.warn(`Access denied from IP: ${clientIP}`);
        return res.status(403).json({
            error: "IP not whitelisted",
            message: "Your IP addredd is not authorized to access this API"
        });
    }
}

// Rate Limiting
function rateLimiter(req, res, next) {
    const apiKey = req.headers['x-api-key'] || req.query.apiKey || 'anonymous';
    const now = Date.now();

    if (!rateLimitMap.has(apiKey)) {
        rateLimitMap.set(apiKey, { count: 1, resetTime: now + RATE_LIMIT_WINDOW });
        return next();
    }

    const limitData = rateLimitMap.get(apiKey);

    if (now > limitData.resetTime) {
        limitData.count = 1;
        limitData.resetTime = now + RATE_LIMIT_WINDOW;
        return next();
    }

    if (limitData.count >= RATE_LIMIT_MAX_REQUESTS) {
        return res.status(429).json({
            error: "Rate limit exceeded",
            message: `Maximum ${RATE_LIMIT_MAX_REQUESTS} requests per minute`,
            retryAfter: Math.ceil((limitData.resetTime - now) / 1000)
        });
    }

    limitData.count++;
    next();
}

const app = express();
app.use(express.json());

app.use((req, res, next) => {
    res.setHeader('X-Content-Type_options', 'nosniff');
    res.setHeader('X-Frame-Options', 'DENY');
    res.setHeader('X-XSS-Protection', '1; mode=block');
    next();
});

app.use(checkIP);
app.use(rateLimiter);

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "client", "index.html"));
});

app.use(express.static(path.join(__dirname, 'client')));

app.get("/api", (req, res) => {
    res.json({
        status: "/api/status",
        pose: "/api/pose",
        config: "/api/config"
    });
});

app.get("/api/status", authAPIKey, (req, res) => {
    res.json({
        status: "boh",
        battery: "-100%",
        sensors: "none"
    });
});

app.get("/api/pose", authAPIKey, (req, res) => {
    res.json({ pose: "correct" });
});

app.get("/api/config", authAPIKey, (req, res) => {
    res.json({ config: "configured" });
});

app.post("/api/tests/servo", authAPIKey, (req, res) => {
    const { angle } = req.body;

    execFile("python", ["main.py", angle], (error, stdout, stderr) => {
        if (error) {
            console.error("Python error: ", stderr);
            return res.status(500).json({ error: "Python script failed" });
        }
        res.json({ ok: true, output: stdout.trim() });
    });
});

app.post("/api/tests/led", authAPIKey, (req, res) => {
    const { state } = req.body;

    if (!state || (state !== "on" && state !== "off")) {
        return res.status(400).json({
            error: "Invalid state. Must provide 'state': 'on' or 'off'"
        });
    }

    execFile("python", ["main.py", state], (error, stdout, stderr) => {
        if (error) {
            console.error("Python error: ", stderr);
            return res.status(500).json({
                error: "Python script failed",
                details: stderr
            });
        }
        res.json({
            ok: true,
            state: state,
            message: `LED turned ${state.toUpperCase()}`,
            output: stdout.trim()
        });
    });
});

app.get("/api/hello", (req, res) => {
    res.json({ message: "Hello from REST" });
});

app.post("/api/emergency-stop", authAPIKey, (req, res) => {
    console.warn("EMERGENCY STOP TRIGGERED");
    res.json({
        message: "Emergency stop activated",
        timeStamp: new Date().toISOString()
    });
});

const server = http.createServer(app);
const wss = new WebSocketServer({ server });

wss.on("connection", (ws, req) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const apiKey = url.searchParams.get('apiKey');

    if (!apiKey || !VALID_API_KEYS.has(apiKey)) {
        console.warn("WebSocket connection rejected: Invalid API key");
        ws.close(1008, "Invalid API key");  // Policy violation
        return;
    }

    const clientIP = req.socket.remoteAddress;
    if (WHITELISTED_IPS.size > 0 && !WHITELISTED_IPS.has(clientIP)) {
        console.warn(`WebSocket connection rejected from IP: ${clientIP}`);
        ws.close(1008, "IP not whitelisted");
        return;
    }

    console.log("WebSocket connected");
    ws.send(JSON.stringify({
        type: "auth",
        status: "authenticated",
        message: "Connected to Quadruped Control WebSocket"
    }));

    ws.on("message", (message) => {
        try {
            const data = JSON.parse(message);
            console.log("Received:", data);

            // Handle different commad types
            if (data.command === "move") {
                ws.send(JSON.stringify({
                    type: "response",
                    command: "move",
                    status: "executed"
                }));
            }

            if (data.command === "stop") {
                ws.send(JSON.stringify({
                    type: "response",
                    command: "stop",
                    status: "executed"
                }));
            }
        } catch (error) {
            ws.send(JSON.stringify({
                type: "error",
                message: "Invalid message format"
            }));
        }
    });

    ws.on("close", () => {
        console.log("WebSocket disconnected");
    });
});

const PORT = 3000;
const HOST = '0.0.0.0';

server.listen(PORT, HOST, () => {
    console.log(`
        REST API:       http://${HOST}:${PORT}
        WebSocket:      ws://${HOST}:${PORT}
        Wifi Access:    http://192.168.4.1:${PORT}    
        `);
});