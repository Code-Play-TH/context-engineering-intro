#!/usr/bin/env python3
"""
Health check script for Factory ERP System Docker container.

Performs comprehensive health checks including:
- HTTP endpoint availability
- Database connectivity
- Critical service status
"""

import os
import sys
import json
import time
import asyncio
import logging
from typing import Dict, Any
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class HealthChecker:
    """Health check implementation."""
    
    def __init__(self):
        """Initialize health checker."""
        self.host = os.environ.get('HOST', '0.0.0.0')
        self.port = os.environ.get('PORT', '8000')
        self.timeout = int(os.environ.get('HEALTH_CHECK_TIMEOUT', '10'))
        self.checks = []
    
    async def check_http_endpoint(self) -> Dict[str, Any]:
        """
        Check if HTTP endpoint is responding.
        
        Returns:
            Dict with check results
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                url = f"http://{self.host}:{self.port}/health"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "name": "http_endpoint",
                            "status": "healthy",
                            "details": {
                                "status_code": response.status,
                                "response_data": data
                            }
                        }
                    else:
                        return {
                            "name": "http_endpoint", 
                            "status": "unhealthy",
                            "details": {
                                "status_code": response.status,
                                "error": f"HTTP {response.status}"
                            }
                        }
                        
        except ImportError:
            # Fallback to urllib if aiohttp not available
            return await self.check_http_endpoint_fallback()
        except Exception as e:
            return {
                "name": "http_endpoint",
                "status": "unhealthy", 
                "details": {"error": str(e)}
            }
    
    async def check_http_endpoint_fallback(self) -> Dict[str, Any]:
        """
        Fallback HTTP check using urllib.
        
        Returns:
            Dict with check results
        """
        try:
            import urllib.request
            import socket
            
            url = f"http://{self.host}:{self.port}/health"
            
            # Set timeout
            socket.setdefaulttimeout(self.timeout)
            
            with urllib.request.urlopen(url) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode())
                    return {
                        "name": "http_endpoint",
                        "status": "healthy",
                        "details": {
                            "status_code": response.getcode(),
                            "response_data": data
                        }
                    }
                else:
                    return {
                        "name": "http_endpoint",
                        "status": "unhealthy",
                        "details": {
                            "status_code": response.getcode(),
                            "error": f"HTTP {response.getcode()}"
                        }
                    }
                    
        except Exception as e:
            return {
                "name": "http_endpoint",
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    async def check_database_connection(self) -> Dict[str, Any]:
        """
        Check database connectivity.
        
        Returns:
            Dict with check results
        """
        try:
            database_url = os.environ.get('DATABASE_URL')
            if not database_url:
                return {
                    "name": "database",
                    "status": "skipped",
                    "details": {"reason": "DATABASE_URL not configured"}
                }
            
            parsed_url = urlparse(database_url)
            
            if parsed_url.scheme.startswith('postgresql'):
                return await self.check_postgresql_connection(database_url)
            elif parsed_url.scheme.startswith('sqlite'):
                return await self.check_sqlite_connection(database_url)
            else:
                return {
                    "name": "database",
                    "status": "skipped", 
                    "details": {"reason": f"Unsupported database scheme: {parsed_url.scheme}"}
                }
                
        except Exception as e:
            return {
                "name": "database",
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    async def check_postgresql_connection(self, database_url: str) -> Dict[str, Any]:
        """
        Check PostgreSQL connection.
        
        Args:
            database_url: Database URL
            
        Returns:
            Dict with check results
        """
        try:
            import asyncpg
            
            parsed = urlparse(database_url)
            
            conn = await asyncpg.connect(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 5432,
                user=parsed.username or 'postgres',
                password=parsed.password or '',
                database=parsed.path.lstrip('/') or 'factory_erp',
                timeout=self.timeout
            )
            
            # Test query
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            
            if result == 1:
                return {
                    "name": "database",
                    "status": "healthy",
                    "details": {"database_type": "postgresql"}
                }
            else:
                return {
                    "name": "database",
                    "status": "unhealthy",
                    "details": {"error": "Test query failed"}
                }
                
        except ImportError:
            return {
                "name": "database",
                "status": "skipped",
                "details": {"reason": "asyncpg not available"}
            }
        except Exception as e:
            return {
                "name": "database",
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    async def check_sqlite_connection(self, database_url: str) -> Dict[str, Any]:
        """
        Check SQLite connection.
        
        Args:
            database_url: Database URL
            
        Returns:
            Dict with check results
        """
        try:
            import aiosqlite
            
            # Extract database path from URL
            if database_url.startswith('sqlite+aiosqlite://'):
                db_path = database_url.replace('sqlite+aiosqlite://', '')
            elif database_url.startswith('sqlite://'):
                db_path = database_url.replace('sqlite://', '')
            else:
                db_path = ':memory:'
            
            async with aiosqlite.connect(db_path) as conn:
                cursor = await conn.execute('SELECT 1')
                result = await cursor.fetchone()
                
                if result and result[0] == 1:
                    return {
                        "name": "database",
                        "status": "healthy",
                        "details": {"database_type": "sqlite"}
                    }
                else:
                    return {
                        "name": "database",
                        "status": "unhealthy",
                        "details": {"error": "Test query failed"}
                    }
                    
        except ImportError:
            return {
                "name": "database",
                "status": "skipped",
                "details": {"reason": "aiosqlite not available"}
            }
        except Exception as e:
            return {
                "name": "database",
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """
        Check available disk space.
        
        Returns:
            Dict with check results
        """
        try:
            import shutil
            
            total, used, free = shutil.disk_usage('/app')
            
            # Convert to percentages
            used_percent = (used / total) * 100
            free_percent = (free / total) * 100
            
            # Consider unhealthy if less than 10% free space
            if free_percent < 10:
                status = "unhealthy"
            elif free_percent < 20:
                status = "warning"
            else:
                status = "healthy"
            
            return {
                "name": "disk_space",
                "status": status,
                "details": {
                    "total_gb": round(total / (1024**3), 2),
                    "used_gb": round(used / (1024**3), 2),
                    "free_gb": round(free / (1024**3), 2),
                    "used_percent": round(used_percent, 1),
                    "free_percent": round(free_percent, 1)
                }
            }
            
        except Exception as e:
            return {
                "name": "disk_space",
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    async def check_memory_usage(self) -> Dict[str, Any]:
        """
        Check memory usage.
        
        Returns:
            Dict with check results
        """
        try:
            # Read memory info from /proc/meminfo
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            # Parse memory values
            mem_total = None
            mem_available = None
            
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) * 1024  # Convert KB to bytes
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) * 1024  # Convert KB to bytes
            
            if mem_total and mem_available:
                used_memory = mem_total - mem_available
                used_percent = (used_memory / mem_total) * 100
                available_percent = (mem_available / mem_total) * 100
                
                # Consider unhealthy if less than 5% available memory
                if available_percent < 5:
                    status = "unhealthy"
                elif available_percent < 15:
                    status = "warning"  
                else:
                    status = "healthy"
                
                return {
                    "name": "memory",
                    "status": status,
                    "details": {
                        "total_mb": round(mem_total / (1024**2), 2),
                        "used_mb": round(used_memory / (1024**2), 2), 
                        "available_mb": round(mem_available / (1024**2), 2),
                        "used_percent": round(used_percent, 1),
                        "available_percent": round(available_percent, 1)
                    }
                }
            else:
                return {
                    "name": "memory",
                    "status": "unhealthy",
                    "details": {"error": "Could not parse memory info"}
                }
                
        except Exception as e:
            return {
                "name": "memory", 
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Returns:
            Dict with overall health status and individual check results
        """
        start_time = time.time()
        
        # Run all checks
        checks = await asyncio.gather(
            self.check_http_endpoint(),
            self.check_database_connection(),
            self.check_disk_space(),
            self.check_memory_usage(),
            return_exceptions=True
        )
        
        # Process results
        results = []
        overall_healthy = True
        
        for check in checks:
            if isinstance(check, Exception):
                results.append({
                    "name": "unknown",
                    "status": "unhealthy",
                    "details": {"error": str(check)}
                })
                overall_healthy = False
            else:
                results.append(check)
                if check.get("status") in ["unhealthy", "error"]:
                    overall_healthy = False
        
        execution_time = round(time.time() - start_time, 3)
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": time.time(),
            "execution_time_seconds": execution_time,
            "checks": results,
            "summary": {
                "total_checks": len(results),
                "healthy_checks": len([r for r in results if r.get("status") == "healthy"]),
                "unhealthy_checks": len([r for r in results if r.get("status") == "unhealthy"]),
                "warning_checks": len([r for r in results if r.get("status") == "warning"]),
                "skipped_checks": len([r for r in results if r.get("status") == "skipped"])
            }
        }


async def main():
    """Main health check function."""
    try:
        checker = HealthChecker()
        results = await checker.run_all_checks()
        
        # Output results as JSON for Docker health check
        if os.environ.get('HEALTH_CHECK_VERBOSE') == 'true':
            print(json.dumps(results, indent=2))
        
        # Exit with appropriate code
        if results["status"] == "healthy":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Health check failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())