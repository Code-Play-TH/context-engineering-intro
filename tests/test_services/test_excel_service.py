"""
Tests for Excel processing service.

Tests Excel file upload, processing, validation, and export functionality.
"""

import pytest
import io
import pandas as pd
from datetime import datetime, timedelta

from app.services.excel_service import ExcelService, ExcelProcessingError


class TestExcelService:
    """Test cases for Excel service."""
    
    @pytest.fixture
    def excel_service(self):
        """Create Excel service instance."""
        return ExcelService()
    
    @pytest.fixture
    def sample_customer_requirements_data(self):
        """Sample customer requirements data for testing."""
        return pd.DataFrame({
            'sale_no': ['SALE001', 'SALE002', 'SALE003'],
            'po_no': ['PO001', 'PO002', 'PO003'],
            'customer_name': ['Customer 1', 'Customer 2', 'Customer 3'],
            'product_part_no': ['PART001', 'PART002', 'PART003'],
            'due_date': [
                datetime.now() + timedelta(days=30),
                datetime.now() + timedelta(days=45),
                datetime.now() + timedelta(days=60)
            ],
            'po_quantity': [100, 200, 150],
            'delivered_quantity': [75, 200, 0],
            'unit_price': [25.50, 45.75, 30.00]
        })
    
    @pytest.fixture
    def sample_products_data(self):
        """Sample products data for testing."""
        return pd.DataFrame({
            'part_no': ['PART001', 'PART002', 'PART003'],
            'part_name': ['Product 1', 'Product 2', 'Product 3'],
            'material_code': ['MAT001', 'MAT002', 'MAT003'],
            'material_description': ['Steel Rod', 'Aluminum Sheet', 'Copper Wire'],
            'unit_of_measure': ['PCS', 'SQM', 'MTR'],
            'standard_cost': [25.50, 45.75, 12.30]
        })
    
    def create_excel_file(self, data: pd.DataFrame) -> io.BytesIO:
        """Helper method to create Excel file from DataFrame."""
        buffer = io.BytesIO()
        data.to_excel(buffer, index=False)
        buffer.seek(0)
        return buffer
    
    @pytest.mark.asyncio
    async def test_process_customer_requirements_valid_data(self, excel_service, sample_customer_requirements_data):
        """Test processing valid customer requirements data."""
        excel_file = self.create_excel_file(sample_customer_requirements_data)
        
        result = await excel_service.process_customer_requirements_upload(
            file=excel_file,
            filename="test_requirements.xlsx",
            validate_only=True
        )
        
        assert result["success"] is True
        assert result["total_rows"] == 3
        assert result["valid_rows"] == 3
        assert result["error_rows"] == 0
        assert len(result["errors"]) == 0
        
        # Check summary calculations
        assert "summary" in result
        summary = result["summary"]
        assert summary["total_po_quantity"] == 450  # 100 + 200 + 150
        assert summary["total_delivered"] == 275    # 75 + 200 + 0
        assert summary["shortage_count"] == 1       # Only SALE003 has shortage
        assert summary["complete_count"] == 2       # SALE001 is partial, SALE002 is complete
    
    @pytest.mark.asyncio
    async def test_process_customer_requirements_missing_columns(self, excel_service):
        """Test processing customer requirements with missing required columns."""
        # Create data with missing columns
        incomplete_data = pd.DataFrame({
            'sale_no': ['SALE001'],
            'customer_name': ['Customer 1']
            # Missing other required columns
        })
        
        excel_file = self.create_excel_file(incomplete_data)
        
        with pytest.raises(ExcelProcessingError) as exc_info:
            await excel_service.process_customer_requirements_upload(
                file=excel_file,
                filename="incomplete.xlsx",
                validate_only=True
            )
        
        assert "Missing required columns" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_process_customer_requirements_invalid_data(self, excel_service):
        """Test processing customer requirements with invalid data."""
        # Create data with invalid values
        invalid_data = pd.DataFrame({
            'sale_no': ['SALE001', 'SALE002'],
            'po_no': ['PO001', 'PO002'],
            'customer_name': ['Customer 1', ''],  # Empty customer name
            'product_part_no': ['PART001', 'PART002'],
            'due_date': ['2024-12-31', 'invalid_date'],  # Invalid date
            'po_quantity': [100, -50],  # Negative quantity
            'delivered_quantity': [75, 'invalid'],  # Invalid number
            'unit_price': [25.50, 30.00]
        })
        
        excel_file = self.create_excel_file(invalid_data)
        
        result = await excel_service.process_customer_requirements_upload(
            file=excel_file,
            filename="invalid.xlsx",
            validate_only=True
        )
        
        assert result["success"] is True
        assert result["total_rows"] == 2
        assert result["valid_rows"] < result["total_rows"]  # Should have errors
        assert result["error_rows"] > 0
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_process_products_valid_data(self, excel_service, sample_products_data):
        """Test processing valid products data."""
        excel_file = self.create_excel_file(sample_products_data)
        
        result = await excel_service.process_product_upload(
            file=excel_file,
            filename="test_products.xlsx",
            validate_only=True
        )
        
        assert result["success"] is True
        assert result["total_rows"] == 3
        assert result["valid_rows"] == 3
        assert result["error_rows"] == 0
        assert len(result["errors"]) == 0
        assert len(result["products"]) == 3
        
        # Verify product data structure
        first_product = result["products"][0]
        assert hasattr(first_product, 'part_no')
        assert hasattr(first_product, 'part_name')
        assert hasattr(first_product, 'standard_cost')
    
    @pytest.mark.asyncio
    async def test_process_products_missing_required_fields(self, excel_service):
        """Test processing products with missing required fields."""
        invalid_data = pd.DataFrame({
            'part_no': ['', 'PART002'],  # Empty part number
            'part_name': ['Product 1', ''],  # Empty part name
            'material_code': ['MAT001', 'MAT002'],
            'standard_cost': [-10, 45.75]  # Negative cost
        })
        
        excel_file = self.create_excel_file(invalid_data)
        
        result = await excel_service.process_product_upload(
            file=excel_file,
            filename="invalid_products.xlsx",
            validate_only=True
        )
        
        assert result["success"] is True
        assert result["error_rows"] == 2  # Both rows have errors
        assert len(result["errors"]) == 2
    
    @pytest.mark.asyncio
    async def test_export_customer_requirements(self, excel_service):
        """Test exporting customer requirements to Excel."""
        # Sample requirements data
        requirements = [
            {
                'sale_no': 'SALE001',
                'po_no': 'PO001',
                'customer_name': 'Customer 1',
                'product_part_no': 'PART001',
                'product_part_name': 'Product 1',
                'due_date': datetime.now(),
                'po_quantity': 100,
                'delivered_quantity': 75,
                'shortage_surplus': -25,
                'summary_status': 'Shortage',
                'unit_price': 25.50,
                'total_value': 2550.00,
                'status': 'pending'
            },
            {
                'sale_no': 'SALE002',
                'po_no': 'PO002',
                'customer_name': 'Customer 2',
                'product_part_no': 'PART002',
                'product_part_name': 'Product 2',
                'due_date': datetime.now(),
                'po_quantity': 200,
                'delivered_quantity': 200,
                'shortage_surplus': 0,
                'summary_status': 'Complete',
                'unit_price': 45.75,
                'total_value': 9150.00,
                'status': 'completed'
            }
        ]
        
        excel_data = await excel_service.export_customer_requirements(
            requirements=requirements,
            include_formulas=True
        )
        
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0
        
        # Verify it's a valid Excel file by reading it back
        excel_buffer = io.BytesIO(excel_data)
        df = pd.read_excel(excel_buffer, sheet_name=0)
        
        assert len(df) == 2
        assert 'Sale No' in df.columns
        assert 'Customer Name' in df.columns
        assert 'Shortage/Surplus' in df.columns
    
    @pytest.mark.asyncio
    async def test_export_customer_requirements_without_formulas(self, excel_service):
        """Test exporting customer requirements without formulas."""
        requirements = [
            {
                'sale_no': 'SALE001',
                'po_no': 'PO001',
                'customer_name': 'Customer 1',
                'product_part_no': 'PART001',
                'product_part_name': 'Product 1',
                'due_date': datetime.now(),
                'po_quantity': 100,
                'delivered_quantity': 75,
                'shortage_surplus': -25,
                'summary_status': 'Shortage',
                'unit_price': 25.50,
                'total_value': 2550.00,
                'status': 'pending'
            }
        ]
        
        excel_data = await excel_service.export_customer_requirements(
            requirements=requirements,
            include_formulas=False
        )
        
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0
        
        # Read back and verify values are static (not formulas)
        excel_buffer = io.BytesIO(excel_data)
        df = pd.read_excel(excel_buffer, sheet_name=0)
        
        assert len(df) == 1
        # When not using formulas, calculated values should be present as static values
    
    @pytest.mark.asyncio
    async def test_export_production_orders(self, excel_service):
        """Test exporting production orders to Excel."""
        orders = [
            {
                'production_order_no': 'PO001',
                'customer_name': 'Customer 1',
                'product_part_no': 'PART001',
                'product_part_name': 'Product 1',
                'planned_quantity': 100,
                'produced_quantity': 75,
                'completion_percentage': 75.0,
                'target_completion_date': datetime.now(),
                'production_status': 'in_progress',
                'priority': 'normal',
                'assigned_to_name': 'John Doe'
            }
        ]
        
        excel_data = await excel_service.export_production_orders(orders=orders)
        
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0
        
        # Verify Excel structure
        excel_buffer = io.BytesIO(excel_data)
        df = pd.read_excel(excel_buffer, sheet_name=0)
        
        assert len(df) == 1
        assert 'Production Order No' in df.columns
        assert 'Completion %' in df.columns
    
    @pytest.mark.asyncio
    async def test_create_vlookup_template(self, excel_service):
        """Test creating VLOOKUP template."""
        excel_data = await excel_service.create_vlookup_template()
        
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0
        
        # Read and verify structure
        excel_buffer = io.BytesIO(excel_data)
        
        # Read product master sheet
        product_df = pd.read_excel(excel_buffer, sheet_name='Product Master')
        assert 'Part No' in product_df.columns
        assert 'Part Name' in product_df.columns
        assert 'Standard Cost' in product_df.columns
        
        # Verify sample data exists
        assert len(product_df) >= 3
        
        # Read customer requirements sheet
        req_df = pd.read_excel(excel_buffer, sheet_name='Customer Requirements')
        assert 'Sale No' in req_df.columns
        assert 'Product Part No' in req_df.columns
        assert 'Product Name' in req_df.columns
    
    @pytest.mark.asyncio
    async def test_excel_processing_error_handling(self, excel_service):
        """Test error handling in Excel processing."""
        # Test with invalid file format
        invalid_file = io.BytesIO(b"This is not an Excel file")
        
        with pytest.raises(ExcelProcessingError):
            await excel_service.process_customer_requirements_upload(
                file=invalid_file,
                filename="not_excel.txt",
                validate_only=True
            )
    
    @pytest.mark.asyncio
    async def test_formula_calculations(self, excel_service, sample_customer_requirements_data):
        """Test that Excel formulas are correctly calculated."""
        excel_file = self.create_excel_file(sample_customer_requirements_data)
        
        result = await excel_service.process_customer_requirements_upload(
            file=excel_file,
            filename="test_formulas.xlsx",
            validate_only=True
        )
        
        assert result["success"] is True
        
        # Verify calculations in summary
        summary = result["summary"]
        
        # Total values should match DataFrame sums
        expected_po_total = sample_customer_requirements_data['po_quantity'].sum()
        expected_delivered_total = sample_customer_requirements_data['delivered_quantity'].sum()
        
        assert summary["total_po_quantity"] == expected_po_total
        assert summary["total_delivered"] == expected_delivered_total
        
        # Verify shortage/surplus calculation
        # In sample data: 75-100=-25, 200-200=0, 0-150=-150
        # So 2 orders have shortage (negative values)
        shortage_count = sum(1 for _, row in sample_customer_requirements_data.iterrows() 
                           if row['delivered_quantity'] - row['po_quantity'] < 0)
        complete_count = sum(1 for _, row in sample_customer_requirements_data.iterrows() 
                           if row['delivered_quantity'] - row['po_quantity'] >= 0)
        
        assert summary["shortage_count"] == shortage_count
        assert summary["complete_count"] == complete_count
    
    def test_excel_service_initialization(self):
        """Test Excel service initialization."""
        service = ExcelService()
        
        # Verify styling objects are created
        assert service.header_font is not None
        assert service.header_fill is not None
        assert service.border is not None
        assert service.center_alignment is not None
        assert service.status_colors is not None
        
        # Verify status colors are defined
        assert "completed" in service.status_colors
        assert "pending" in service.status_colors
        assert "shortage" in service.status_colors