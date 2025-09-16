#!/usr/bin/env python3
"""
Initial data seeding script for KOL Management System
Seeds production-ready initial data including authentication setup.
"""

import asyncio
import logging
from datetime import datetime

from app.core.database import get_session
from app.utils.auth_seeder import AuthSeeder, seed_auth_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_production_data():
    """
    Seed production data for the KOL Management System.
    """
    logger.info("Starting production data seeding...")

    try:
        # Seed authentication data
        logger.info("Seeding authentication data...")
        auth_results = await seed_auth_data()

        logger.info("Authentication seeding results:")
        logger.info(f"  - Permissions: {auth_results['permissions']}")
        logger.info(f"  - Roles: {auth_results['roles']}")
        logger.info(f"  - Role-Permission assignments: {auth_results['role_permissions']}")
        logger.info(f"  - Default users: {auth_results['default_users']}")

        logger.info("✅ Production data seeding completed successfully!")

    except Exception as e:
        logger.error(f"❌ Data seeding failed: {e}")
        raise


def main():
    """Main entry point for the seeding script."""
    try:
        asyncio.run(seed_production_data())
    except KeyboardInterrupt:
        logger.info("Seeding interrupted by user")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()