#!/usr/bin/env node

/**
 * Simple service connectivity test for KOL Management System
 * Tests PostgreSQL and Redis connectivity via Docker containers
 */

const http = require('http');
const { exec } = require('child_process');
const util = require('util');

const execAsync = util.promisify(exec);

class ServiceTester {
    constructor() {
        this.results = {
            postgres: { status: 'unknown', details: null },
            redis: { status: 'unknown', details: null },
            ports: { status: 'unknown', details: null }
        };
    }

    async testPostgreSQL() {
        console.log('🔍 Testing PostgreSQL connectivity...');
        try {
            const { stdout, stderr } = await execAsync(
                'docker exec kol_postgres_dev pg_isready -U koluser -d kolsystem_dev'
            );

            if (stdout.includes('accepting connections')) {
                this.results.postgres = { status: 'healthy', details: stdout.trim() };
                console.log('✅ PostgreSQL is healthy');

                // Test basic query
                const { stdout: version } = await execAsync(
                    'docker exec kol_postgres_dev psql -U koluser -d kolsystem_dev -c "SELECT version();" -t'
                );
                console.log(`   Database version: ${version.trim().substring(0, 50)}...`);

            } else {
                throw new Error('PostgreSQL not ready');
            }
        } catch (error) {
            this.results.postgres = { status: 'error', details: error.message };
            console.log('❌ PostgreSQL connection failed:', error.message);
        }
    }

    async testRedis() {
        console.log('🔍 Testing Redis connectivity...');
        try {
            const { stdout } = await execAsync('docker exec kol_redis_dev redis-cli ping');

            if (stdout.trim() === 'PONG') {
                this.results.redis = { status: 'healthy', details: 'PONG received' };
                console.log('✅ Redis is healthy');

                // Get Redis info
                const { stdout: info } = await execAsync(
                    'docker exec kol_redis_dev redis-cli info server | head -2'
                );
                console.log(`   Redis version: ${info.split('\n')[1]}`);

            } else {
                throw new Error('Redis did not respond with PONG');
            }
        } catch (error) {
            this.results.redis = { status: 'error', details: error.message };
            console.log('❌ Redis connection failed:', error.message);
        }
    }

    async testPorts() {
        console.log('🔍 Testing port accessibility...');
        const ports = [
            { name: 'PostgreSQL', port: 5432, host: 'localhost' },
            { name: 'Redis', port: 6380, host: 'localhost' }
        ];

        const portResults = [];

        for (const { name, port, host } of ports) {
            try {
                await this.checkPort(host, port);
                portResults.push(`${name}:${port} ✅`);
                console.log(`   ✅ ${name} port ${port} is accessible`);
            } catch (error) {
                portResults.push(`${name}:${port} ❌`);
                console.log(`   ❌ ${name} port ${port} is not accessible`);
            }
        }

        this.results.ports = {
            status: portResults.every(r => r.includes('✅')) ? 'healthy' : 'partial',
            details: portResults.join(', ')
        };
    }

    checkPort(host, port) {
        return new Promise((resolve, reject) => {
            const socket = require('net').createConnection(port, host);

            socket.on('connect', () => {
                socket.destroy();
                resolve();
            });

            socket.on('error', (error) => {
                reject(error);
            });

            socket.setTimeout(3000, () => {
                socket.destroy();
                reject(new Error('Connection timeout'));
            });
        });
    }

    async testDockerContainers() {
        console.log('🔍 Checking Docker container status...');
        try {
            const { stdout } = await execAsync('docker ps --filter "name=kol_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"');
            console.log('\n📋 Docker Container Status:');
            console.log(stdout);
        } catch (error) {
            console.log('❌ Failed to get Docker status:', error.message);
        }
    }

    async runAllTests() {
        console.log('🚀 Starting KOL Management System Service Tests\n');
        console.log('=' * 60);

        await this.testDockerContainers();
        console.log('\n' + '=' * 60);

        await this.testPostgreSQL();
        await this.testRedis();
        await this.testPorts();

        console.log('\n' + '=' * 60);
        console.log('📊 Test Results Summary:');
        console.log('=' * 60);

        Object.entries(this.results).forEach(([service, result]) => {
            const icon = result.status === 'healthy' ? '✅' :
                        result.status === 'partial' ? '⚠️' : '❌';
            console.log(`${icon} ${service.toUpperCase()}: ${result.status}`);
            if (result.details) {
                console.log(`   Details: ${result.details}`);
            }
        });

        const allHealthy = Object.values(this.results).every(r => r.status === 'healthy');

        console.log('\n' + '=' * 60);
        if (allHealthy) {
            console.log('🎉 All services are healthy! System is ready for testing.');
        } else {
            console.log('⚠️  Some services have issues. Check the details above.');
        }
        console.log('=' * 60);

        return allHealthy;
    }
}

// Run the tests
if (require.main === module) {
    const tester = new ServiceTester();
    tester.runAllTests()
        .then(success => {
            process.exit(success ? 0 : 1);
        })
        .catch(error => {
            console.error('❌ Test suite failed:', error);
            process.exit(1);
        });
}

module.exports = ServiceTester;