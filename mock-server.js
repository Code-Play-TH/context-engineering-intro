#!/usr/bin/env node

/**
 * Mock KOL Management System API Server
 * Simple Node.js server to simulate the basic API endpoints for testing
 */

const http = require('http');
const url = require('url');

class MockKOLServer {
    constructor(port = 8000) {
        this.port = port;
        this.server = null;
    }

    start() {
        this.server = http.createServer((req, res) => {
            const parsedUrl = url.parse(req.url, true);
            const path = parsedUrl.pathname;
            const method = req.method;

            // Set CORS headers
            res.setHeader('Access-Control-Allow-Origin', '*');
            res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
            res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
            res.setHeader('Content-Type', 'application/json');

            // Handle preflight requests
            if (method === 'OPTIONS') {
                res.writeHead(200);
                res.end();
                return;
            }

            try {
                this.handleRequest(req, res, path, method);
            } catch (error) {
                console.error('Request error:', error);
                res.writeHead(500);
                res.end(JSON.stringify({
                    error: 'Internal server error',
                    message: error.message
                }));
            }
        });

        this.server.listen(this.port, () => {
            console.log(`🚀 Mock KOL API Server running at http://localhost:${this.port}`);
            console.log('📋 Available endpoints:');
            console.log('   GET  /health - Health check');
            console.log('   GET  /health/detailed - Detailed health check');
            console.log('   GET  /info - API information');
            console.log('   GET  / - API root');
            console.log('   GET  /api/v1/kols - List KOLs');
            console.log('   POST /api/v1/kols - Create KOL');
            console.log('   GET  /api/v1/campaigns - List campaigns');
            console.log('   POST /api/v1/campaigns - Create campaign');
            console.log('   GET  /docs - API documentation (mock)');
        });

        return this;
    }

    handleRequest(req, res, path, method) {
        const timestamp = new Date().toISOString();

        // Log request
        console.log(`${timestamp} ${method} ${path}`);

        // Route handling
        if (path === '/health') {
            this.handleHealth(res);
        } else if (path === '/health/detailed') {
            this.handleDetailedHealth(res);
        } else if (path === '/info') {
            this.handleInfo(res);
        } else if (path === '/') {
            this.handleRoot(res);
        } else if (path === '/docs') {
            this.handleDocs(res);
        } else if (path.startsWith('/api/v1/kols')) {
            this.handleKOLs(req, res, method);
        } else if (path.startsWith('/api/v1/campaigns')) {
            this.handleCampaigns(req, res, method);
        } else {
            this.handle404(res, path);
        }
    }

    handleHealth(res) {
        res.writeHead(200);
        res.end(JSON.stringify({
            status: "healthy",
            service: "KOL Management System API (Mock)",
            version: "1.0.0",
            timestamp: new Date().toISOString()
        }));
    }

    handleDetailedHealth(res) {
        res.writeHead(200);
        res.end(JSON.stringify({
            status: "healthy",
            service: "KOL Management System API (Mock)",
            version: "1.0.0",
            components: {
                database: "healthy",
                redis: "healthy",
                task_system: "healthy"
            },
            task_queues: {
                default: 0,
                email: 0,
                social_media: 0
            },
            active_workers: 1,
            timestamp: new Date().toISOString()
        }));
    }

    handleInfo(res) {
        res.writeHead(200);
        res.end(JSON.stringify({
            name: "KOL Management System API (Mock)",
            version: "1.0.0",
            description: "Comprehensive KOL Influencer Management System",
            features: [
                "KOL Profile Management",
                "Social Media Integration",
                "Campaign Management",
                "Multi-channel Communication",
                "Performance Analytics",
                "Content Monitoring",
                "Background Task Processing"
            ],
            supported_platforms: [
                "Instagram",
                "YouTube",
                "TikTok",
                "Twitter",
                "Facebook"
            ],
            communication_channels: [
                "Email",
                "Discord",
                "Line Messaging"
            ]
        }));
    }

    handleRoot(res) {
        res.writeHead(200);
        res.end(JSON.stringify({
            message: "Welcome to the KOL Management System API (Mock)",
            version: "1.0.0",
            documentation: "/docs",
            health: "/health",
            info: "/info",
            endpoints: {
                kols: "/api/v1/kols",
                campaigns: "/api/v1/campaigns"
            }
        }));
    }

    handleDocs(res) {
        res.writeHead(200);
        res.setHeader('Content-Type', 'text/html');
        res.end(`
            <html>
                <head><title>KOL API Documentation (Mock)</title></head>
                <body>
                    <h1>KOL Management System API Documentation</h1>
                    <p>This is a mock server for testing purposes.</p>
                    <h2>Available Endpoints:</h2>
                    <ul>
                        <li>GET /health - Health check</li>
                        <li>GET /health/detailed - Detailed health check</li>
                        <li>GET /info - API information</li>
                        <li>GET /api/v1/kols - List KOLs</li>
                        <li>POST /api/v1/kols - Create KOL</li>
                        <li>GET /api/v1/campaigns - List campaigns</li>
                        <li>POST /api/v1/campaigns - Create campaign</li>
                    </ul>
                </body>
            </html>
        `);
    }

    handleKOLs(req, res, method) {
        if (method === 'GET') {
            res.writeHead(200);
            res.end(JSON.stringify({
                data: [
                    {
                        id: 1,
                        name: "Demo KOL 1",
                        email: "kol1@example.com",
                        platforms: ["Instagram", "YouTube"],
                        followers: 50000,
                        engagement_rate: 3.5,
                        status: "active"
                    },
                    {
                        id: 2,
                        name: "Demo KOL 2",
                        email: "kol2@example.com",
                        platforms: ["TikTok", "Twitter"],
                        followers: 75000,
                        engagement_rate: 4.2,
                        status: "active"
                    }
                ],
                total: 2,
                page: 1,
                per_page: 10
            }));
        } else if (method === 'POST') {
            res.writeHead(201);
            res.end(JSON.stringify({
                message: "KOL created successfully (mock)",
                id: Math.floor(Math.random() * 1000) + 100,
                status: "created"
            }));
        } else {
            res.writeHead(405);
            res.end(JSON.stringify({ error: "Method not allowed" }));
        }
    }

    handleCampaigns(req, res, method) {
        if (method === 'GET') {
            res.writeHead(200);
            res.end(JSON.stringify({
                data: [
                    {
                        id: 1,
                        name: "Summer Campaign 2024",
                        description: "Summer product promotion",
                        status: "active",
                        kol_count: 5,
                        start_date: "2024-06-01",
                        end_date: "2024-08-31"
                    },
                    {
                        id: 2,
                        name: "Back to School Campaign",
                        description: "Educational product promotion",
                        status: "planning",
                        kol_count: 3,
                        start_date: "2024-09-01",
                        end_date: "2024-10-31"
                    }
                ],
                total: 2,
                page: 1,
                per_page: 10
            }));
        } else if (method === 'POST') {
            res.writeHead(201);
            res.end(JSON.stringify({
                message: "Campaign created successfully (mock)",
                id: Math.floor(Math.random() * 1000) + 100,
                status: "created"
            }));
        } else {
            res.writeHead(405);
            res.end(JSON.stringify({ error: "Method not allowed" }));
        }
    }

    handle404(res, path) {
        res.writeHead(404);
        res.end(JSON.stringify({
            error: "Not Found",
            message: `The requested resource '${path}' was not found`,
            available_endpoints: ["/health", "/info", "/api/v1/kols", "/api/v1/campaigns"]
        }));
    }

    stop() {
        if (this.server) {
            this.server.close();
            console.log('🛑 Mock server stopped');
        }
    }
}

// Start server if run directly
if (require.main === module) {
    const server = new MockKOLServer(8001);
    server.start();

    // Graceful shutdown
    process.on('SIGINT', () => {
        console.log('\n📢 Received SIGINT, shutting down gracefully...');
        server.stop();
        process.exit(0);
    });

    process.on('SIGTERM', () => {
        console.log('\n📢 Received SIGTERM, shutting down gracefully...');
        server.stop();
        process.exit(0);
    });
}

module.exports = MockKOLServer;