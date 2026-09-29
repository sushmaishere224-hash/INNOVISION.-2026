import { createServer, request as httpRequest } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)));
const port = Number(process.env.PORT || 5173);
const backendTarget = process.env.BACKEND_URL || "http://127.0.0.1:8000";

const contentTypes = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".json": "application/json",
};

createServer(async (req, res) => {
    let parsedUrl;
    try {
        parsedUrl = new URL(req.url, "http://localhost");
    } catch {
        res.writeHead(400).end("Bad request");
        return;
    }

    const pathname = decodeURIComponent(parsedUrl.pathname);

    // API Reverse Proxy to FastAPI Backend
    if (pathname.startsWith("/api/")) {
        const backendPath = pathname.replace(/^\/api/, "") + (parsedUrl.search || "");
        const targetUrl = new URL(backendPath, backendTarget);

        const proxyReq = httpRequest(
            targetUrl,
            {
                method: req.method,
                headers: {
                    ...req.headers,
                    host: targetUrl.host,
                },
            },
            (backendRes) => {
                res.writeHead(backendRes.statusCode || 500, backendRes.headers);
                backendRes.pipe(res, { end: true });
            }
        );

        proxyReq.on("error", (err) => {
            console.error("API proxy error:", err.message);
            res.writeHead(502, { "Content-Type": "application/json" });
            res.end(JSON.stringify({ error: "Backend service unreachable", details: err.message }));
        });

        req.pipe(proxyReq, { end: true });
        return;
    }

    if (req.method !== "GET" && req.method !== "HEAD") {
        res.writeHead(405, { Allow: "GET, HEAD" }).end();
        return;
    }

    const filePath = resolve(root, `.${pathname === "/" ? "/main.html" : pathname}`);
    if (filePath !== root && !filePath.startsWith(`${root}${sep}`)) {
        res.writeHead(403).end("Forbidden");
        return;
    }

    try {
        const content = await readFile(filePath);
        res.writeHead(200, { "Content-Type": contentTypes[extname(filePath)] || "application/octet-stream" });
        res.end(req.method === "HEAD" ? undefined : content);
    } catch {
        res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" }).end("Not found");
    }
}).listen(port, () => {
    console.log(`Earth, in Orbit (Frontend): http://localhost:${port}`);
    console.log(`Proxying /api to Backend: ${backendTarget}`);
});