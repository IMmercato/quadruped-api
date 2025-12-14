import express from "express";
import http from "http";
import path from "path";
import { execFile } from "child_process";
import { WebSocketServer } from "ws";
import { fileURLToPath } from "url";
import { dirname } from "path";
import { error } from "console";
import { stderr, stdout } from "process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
app.use(express.json());

app.use(express.static(path.join(__dirname, 'client')));

app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "client", "index.html"));
});

app.get("/api/status", (req, res) => {
    res.json({
        status: "boh",
        battery: "-100%",
        sensors: "none"
    });
});

app.get("/api/pose", (req, res) => {
    res.json({ pose: "correct" });
});

app.get("/api/config", (req, res) => {
    res.json({ config: "configured" });
});

app.post("/api/tests/servo", (req, res) => {
    const { angle } = req.body;

    execFile("python", ["main.py", angle], (error, stdout, stderr) => {
        if (error) {
            console.error("Python error: ", stderr);
            return res.status(500).json({ error: "Python script failed" });
        }
        res.json({ ok: true, output: stdout.trim() });
    });
});

app.post("/api/tests/led", (req, res) => {
    const { state } = req.body;

    if(!state || (state !== "on" && state !== "off")) {
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

const server = http.createServer(app);

const wss = new WebSocketServer({ server });

wss.on("connection", (ws) => {
    console.log("WS connected");
    ws.send("Hello from WebSocket");
});

server.listen(3000, () => {
    console.log("Server running on http://localhost:3000");
});