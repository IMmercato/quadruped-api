import express from "express";
import http from "http";
import { execFile } from "child_process";
import { WebSocketServer } from "ws";
import { stderr, stdout } from "process";

const app = express();
app.use(express.json());

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

app.post("/api/test-servo", (req, res) => {
    const { angle } = req.body;

    execFile("python", ["main.py", angle], (error, stdout, stderr) => {
        if (error) {
            console.error("Python error: ", stderr);
            return res.status(500).json({ error: "Python script failed" });
        }
        res.json({ ok: true, output: stdout.trim() });
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