"""
Performance and Load Tests

Tests for system performance under various load conditions.
"""

import pytest
import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.services.content_monitoring.content_monitor import ContentMonitorService
from app.services.analytics.analytics_engine import AnalyticsEngine
from app.services.analytics.roi_calculator import ROICalculator
from app.models.kol import KOL, KOLStatus
from app.models.campaign import Campaign, CampaignStatus


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def performance_test_data():
    """Generate test data for performance testing."""

    # Generate multiple KOLs
    kols = []
    for i in range(100):
        kol = KOL(
            id=i + 1,
            name=f"Test KOL {i + 1}",
            email=f"kol{i + 1}@example.com",
            social_media_accounts={
                "instagram": {"handle": f"kol_{i + 1}", "verified": i % 10 == 0},
                "youtube": {"handle": f"kol_{i + 1}_yt", "verified": i % 15 == 0}
            },
            niche=["fashion", "lifestyle", "beauty"][i % 3:i % 3 + 1],
            status=KOLStatus.ACTIVE,
            follower_counts={
                "instagram": 10000 + (i * 1000),
                "youtube": 5000 + (i * 500)
            },
            engagement_rates={
                "instagram": 0.03 + (i * 0.001),
                "youtube": 0.02 + (i * 0.0005)
            }
        )
        kols.append(kol)

    # Generate multiple campaigns
    campaigns = []
    for i in range(20):
        campaign = Campaign(
            id=i + 1,
            name=f"Performance Test Campaign {i + 1}",
            description=f"Campaign {i + 1} for performance testing",
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow() + timedelta(days=30),
            status=CampaignStatus.ACTIVE,
            target_kpis={
                "total_reach": 100000 + (i * 10000),
                "engagement_rate": 0.05,
                "roi_percentage": 200 + (i * 10)
            }
        )
        campaigns.append(campaign)

    return {"kols": kols, "campaigns": campaigns}


class TestPerformanceUnderLoad:
    """Performance tests under various load conditions."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_content_monitoring_performance_100_kols(
        self,
        mock_db,
        performance_test_data
    ):
        """Test content monitoring performance with 100 KOLs."""

        with patch('app.services.content_monitoring.content_monitor.AIContentAnalyzer'), \
             patch('app.services.content_monitoring.content_monitor.SocialMediaServiceFactory'):

            content_monitor = ContentMonitorService(mock_db)
            kols = performance_test_data["kols"]
            campaign = performance_test_data["campaigns"][0]

            # Mock social media service responses
            mock_service = AsyncMock()
            mock_service.get_recent_posts.return_value = []  # Empty for performance testing
            content_monitor.social_media_factory.get_service.return_value = mock_service

            # Measure performance
            start_time = time.time()

            # Process KOLs in batches to simulate real-world usage
            batch_size = 10
            processing_times = []

            for i in range(0, len(kols), batch_size):
                batch = kols[i:i + batch_size]
                batch_start = time.time()

                # Process batch concurrently
                tasks = [
                    content_monitor.detect_new_content(kol, campaign)
                    for kol in batch
                ]
                await asyncio.gather(*tasks)

                batch_time = time.time() - batch_start
                processing_times.append(batch_time)

            total_time = time.time() - start_time

            # Performance assertions
            assert total_time < 30.0  # Should complete within 30 seconds
            assert max(processing_times) < 5.0  # No batch should take more than 5 seconds
            assert statistics.mean(processing_times) < 3.0  # Average batch time under 3 seconds

            print(f"Content monitoring performance:")
            print(f"  Total time for 100 KOLs: {total_time:.2f}s")
            print(f"  Average batch time: {statistics.mean(processing_times):.2f}s")
            print(f"  Max batch time: {max(processing_times):.2f}s")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_analytics_performance_concurrent_calculations(
        self,
        performance_test_data
    ):
        """Test analytics performance with concurrent ROI calculations."""

        roi_calculator = ROICalculator()
        campaigns_data = []

        # Prepare campaign data for ROI calculations
        for i, campaign in enumerate(performance_test_data["campaigns"][:10]):
            campaign_data = {
                "campaign_id": campaign.id,
                "industry": "fashion",
                "kol_payments": [
                    {"amount": 1000 + (i * 100), "currency_rate": 1.0},
                    {"amount": 1500 + (i * 150), "currency_rate": 1.0}
                ],
                "content_posts": [
                    {
                        "platform": "instagram",
                        "likes": 1000 + (i * 100),
                        "comments": 50 + (i * 5),
                        "shares": 20 + (i * 2),
                        "reach": 10000 + (i * 1000),
                        "posted_at": datetime.utcnow()
                    }
                ],
                "direct_sales": [{"value": 2000 + (i * 200)}]
            }
            campaigns_data.append(campaign_data)

        # Measure concurrent ROI calculations
        start_time = time.time()

        tasks = [
            roi_calculator.calculate_campaign_roi(data)
            for data in campaigns_data
        ]

        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Performance assertions
        assert total_time < 10.0  # Should complete within 10 seconds
        assert len(results) == 10  # All calculations should complete
        assert all(result.roi_metrics["roi_percentage"] is not None for result in results)

        print(f"ROI calculation performance:")
        print(f"  10 concurrent calculations: {total_time:.2f}s")
        print(f"  Average per calculation: {total_time/10:.2f}s")

    @pytest.mark.performance
    def test_database_query_performance_simulation(self, mock_db):
        """Test database query performance simulation."""

        # Simulate database query latencies
        query_times = []

        def simulate_db_query(query_type: str) -> float:
            """Simulate different types of database queries."""
            base_times = {
                "simple_select": 0.001,
                "complex_join": 0.050,
                "aggregation": 0.100,
                "bulk_insert": 0.200
            }

            import random
            base_time = base_times.get(query_type, 0.010)
            # Add some variance to simulate real-world conditions
            variance = random.uniform(0.8, 1.2)
            return base_time * variance

        # Simulate mixed workload
        operations = [
            ("simple_select", 100),  # 100 simple selects
            ("complex_join", 20),    # 20 complex joins
            ("aggregation", 10),     # 10 aggregations
            ("bulk_insert", 5)       # 5 bulk inserts
        ]

        start_time = time.time()

        for operation_type, count in operations:
            for _ in range(count):
                query_time = simulate_db_query(operation_type)
                query_times.append(query_time)
                time.sleep(query_time)  # Simulate actual query time

        total_time = time.time() - start_time

        # Performance assertions
        assert total_time < 15.0  # Should complete within 15 seconds
        assert statistics.mean(query_times) < 0.1  # Average query under 100ms
        assert max(query_times) < 0.5  # No query over 500ms

        print(f"Database performance simulation:")
        print(f"  Total time for 135 queries: {total_time:.2f}s")
        print(f"  Average query time: {statistics.mean(query_times)*1000:.1f}ms")
        print(f"  Max query time: {max(query_times)*1000:.1f}ms")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, performance_test_data):
        """Test memory usage under load conditions."""

        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large dataset in memory
        large_dataset = []
        kols = performance_test_data["kols"]

        # Simulate processing large amounts of data
        for kol in kols:
            # Create multiple data points for each KOL
            for i in range(50):  # 50 data points per KOL
                data_point = {
                    "kol_id": kol.id,
                    "timestamp": datetime.utcnow() - timedelta(days=i),
                    "metrics": {
                        "followers": kol.follower_counts,
                        "engagement": kol.engagement_rates,
                        "content_count": i * 2,
                        "performance_score": i * 0.1
                    }
                }
                large_dataset.append(data_point)

        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # Clean up
        del large_dataset

        # Memory assertions
        assert memory_increase < 500  # Should not use more than 500MB additional memory

        print(f"Memory usage test:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Peak memory: {peak_memory:.1f}MB")
        print(f"  Memory increase: {memory_increase:.1f}MB")

    @pytest.mark.performance
    def test_concurrent_api_requests_simulation(self):
        """Test system performance under concurrent API requests."""

        def simulate_api_request(request_type: str) -> dict:
            """Simulate different types of API requests."""
            import random
            import time

            # Simulate request processing time
            processing_times = {
                "get_kol": random.uniform(0.05, 0.15),
                "get_campaign": random.uniform(0.08, 0.20),
                "create_content": random.uniform(0.20, 0.50),
                "calculate_roi": random.uniform(0.30, 0.80),
                "generate_report": random.uniform(1.0, 3.0)
            }

            time.sleep(processing_times.get(request_type, 0.1))

            return {
                "request_type": request_type,
                "processing_time": processing_times.get(request_type, 0.1),
                "status": "success"
            }

        # Simulate concurrent load
        request_mix = [
            ("get_kol", 30),
            ("get_campaign", 20),
            ("create_content", 15),
            ("calculate_roi", 10),
            ("generate_report", 5)
        ]

        all_requests = []
        for request_type, count in request_mix:
            all_requests.extend([request_type] * count)

        start_time = time.time()
        results = []

        # Use ThreadPoolExecutor to simulate concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(simulate_api_request, request_type)
                for request_type in all_requests
            ]

            for future in as_completed(futures):
                results.append(future.result())

        total_time = time.time() - start_time

        # Performance assertions
        assert total_time < 30.0  # Should handle 80 requests within 30 seconds
        assert len(results) == 80  # All requests should complete
        assert all(result["status"] == "success" for result in results)

        # Calculate performance metrics
        processing_times = [result["processing_time"] for result in results]

        print(f"Concurrent API performance:")
        print(f"  80 requests completed in: {total_time:.2f}s")
        print(f"  Average processing time: {statistics.mean(processing_times):.2f}s")
        print(f"  Throughput: {len(results)/total_time:.1f} requests/second")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_social_media_api_rate_limiting_performance(self, mock_db):
        """Test performance under social media API rate limiting conditions."""

        with patch('app.services.content_monitoring.content_monitor.AIContentAnalyzer'), \
             patch('app.services.content_monitoring.content_monitor.SocialMediaServiceFactory'):

            content_monitor = ContentMonitorService(mock_db)

            # Mock rate-limited social media service
            mock_service = AsyncMock()

            call_count = 0
            async def rate_limited_get_posts(*args, **kwargs):
                nonlocal call_count
                call_count += 1

                # Simulate rate limiting every 5th call
                if call_count % 5 == 0:
                    await asyncio.sleep(1.0)  # Simulate rate limit delay

                return []  # Return empty for testing

            mock_service.get_recent_posts.side_effect = rate_limited_get_posts
            content_monitor.social_media_factory.get_service.return_value = mock_service

            # Test with multiple KOLs
            test_kols = [
                KOL(
                    id=i,
                    name=f"Test KOL {i}",
                    email=f"test{i}@example.com",
                    social_media_accounts={"instagram": {"handle": f"test{i}"}},
                    niche=["test"],
                    status=KOLStatus.ACTIVE
                )
                for i in range(20)
            ]

            test_campaign = Campaign(
                id=1,
                name="Rate Limit Test Campaign",
                description="Testing rate limits",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
                status=CampaignStatus.ACTIVE
            )

            start_time = time.time()

            # Process all KOLs
            tasks = [
                content_monitor.detect_new_content(kol, test_campaign)
                for kol in test_kols
            ]
            await asyncio.gather(*tasks)

            total_time = time.time() - start_time

            # Performance assertions with rate limiting
            assert total_time < 15.0  # Should complete within 15 seconds even with rate limits
            assert call_count == 20  # Should make exactly 20 API calls

            print(f"Rate limiting performance:")
            print(f"  20 KOLs processed in: {total_time:.2f}s")
            print(f"  API calls made: {call_count}")
            print(f"  Average time per KOL: {total_time/20:.2f}s")

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_dataset_analytics_performance(self):
        """Test analytics performance with large datasets."""

        # Create large dataset
        large_campaign_data = {
            "campaign_id": 1,
            "industry": "fashion",
            "kol_payments": [
                {"amount": 1000 + i, "currency_rate": 1.0}
                for i in range(50)  # 50 KOL payments
            ],
            "content_posts": [
                {
                    "platform": ["instagram", "youtube", "tiktok"][i % 3],
                    "likes": 1000 + (i * 10),
                    "comments": 50 + i,
                    "shares": 20 + (i // 2),
                    "reach": 10000 + (i * 100),
                    "posted_at": datetime.utcnow() - timedelta(days=i % 30)
                }
                for i in range(500)  # 500 content posts
            ],
            "direct_sales": [
                {"value": 100 + (i * 5)}
                for i in range(200)  # 200 sales transactions
            ]
        }

        roi_calculator = ROICalculator()

        start_time = time.time()

        # Calculate ROI with large dataset
        result = await roi_calculator.calculate_campaign_roi(large_campaign_data)

        calculation_time = time.time() - start_time

        # Performance assertions
        assert calculation_time < 5.0  # Should complete within 5 seconds
        assert result.total_investment > 0
        assert result.total_value_generated > 0
        assert result.confidence_score > 0

        print(f"Large dataset analytics performance:")
        print(f"  Dataset size: 50 payments, 500 posts, 200 sales")
        print(f"  Calculation time: {calculation_time:.2f}s")
        print(f"  ROI calculated: {result.roi_metrics['roi_percentage']:.1f}%")