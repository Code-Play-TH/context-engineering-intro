"""
Excel processing service for import/export operations.

Handles Excel file uploads, data validation, and export functionality.
"""

import io
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional, BinaryIO
from pathlib import Path

import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.formatting.rule import DataBarRule
from openpyxl.worksheet.datavalidation import DataValidation

from app.config import get_settings
from app.models.sales import CustomerRequirement, Customer
from app.models.production import ProductionOrder
from app.models.product import Product
from app.schemas.sales import CustomerRequirementCreate, CustomerCreate
from app.schemas.production import ProductionOrderCreate
from app.schemas.product import ProductCreate, ProductionStepBase

settings = get_settings()


class ExcelProcessingError(Exception):
    """Custom exception for Excel processing errors."""
    pass


class ExcelService:
    """
    Service for handling Excel file processing operations.
    
    Provides functionality for importing and exporting Excel files
    with data validation and formatting.
    """
    
    def __init__(self):
        """Initialize Excel service with standard formatting styles."""
        # Standard cell styles
        self.header_font = Font(bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )
        self.center_alignment = Alignment(horizontal="center", vertical="center")
        
        # Status-based formatting
        self.status_colors = {
            "completed": "90EE90",  # Light green
            "pending": "FFE4B5",    # Moccasin
            "partial": "FFA500",    # Orange
            "overdue": "FFB6C1",    # Light pink
            "shortage": "FF6B6B",   # Red
        }
    
    async def process_customer_requirements_upload(
        self, 
        file: BinaryIO, 
        filename: str,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Process uploaded Excel file containing customer requirements.
        
        Args:
            file: Excel file binary data
            filename: Original filename
            validate_only: If True, only validate data without processing
            
        Returns:
            Dict containing processing results and any errors
            
        Raises:
            ExcelProcessingError: If file processing fails
        """
        try:
            # Read Excel file
            df = pd.read_excel(file, sheet_name=0)
            
            # Validate required columns
            required_columns = [
                "sale_no", "po_no", "customer_name", "product_part_no",
                "due_date", "po_quantity", "delivered_quantity", "unit_price"
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ExcelProcessingError(f"Missing required columns: {missing_columns}")
            
            # Clean and validate data
            df = df.dropna(subset=["sale_no", "po_no", "customer_name"])
            
            # Convert data types
            df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")
            df["po_quantity"] = pd.to_numeric(df["po_quantity"], errors="coerce")
            df["delivered_quantity"] = pd.to_numeric(df["delivered_quantity"], errors="coerce")
            df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
            
            # Fill missing values
            df["delivered_quantity"] = df["delivered_quantity"].fillna(0)
            df["unit_price"] = df["unit_price"].fillna(0)
            
            # Calculate derived fields
            df["shortage_surplus"] = df["delivered_quantity"] - df["po_quantity"]
            df["summary_status"] = df["shortage_surplus"].apply(
                lambda x: "Complete" if x >= 0 else "Shortage"
            )
            df["total_value"] = df["po_quantity"] * df["unit_price"]
            
            # Validate data
            errors = []
            valid_rows = []
            
            for index, row in df.iterrows():
                row_errors = []
                
                # Validate required fields
                if pd.isna(row["due_date"]):
                    row_errors.append("Invalid due_date")
                if pd.isna(row["po_quantity"]) or row["po_quantity"] <= 0:
                    row_errors.append("Invalid po_quantity")
                if row["delivered_quantity"] < 0:
                    row_errors.append("Invalid delivered_quantity")
                
                if row_errors:
                    errors.append({
                        "row": index + 2,  # Excel row number (1-based + header)
                        "sale_no": row["sale_no"],
                        "errors": row_errors
                    })
                else:
                    valid_rows.append(row)
            
            # Create CustomerRequirementCreate objects
            customer_requirements = []
            if not validate_only:
                for row in valid_rows:
                    req_data = CustomerRequirementCreate(
                        sale_no=str(row["sale_no"]),
                        po_no=str(row["po_no"]),
                        customer_name=str(row["customer_name"]),
                        product_id=1,  # TODO: Implement product lookup by part_no
                        due_date=row["due_date"],
                        po_quantity=int(row["po_quantity"]),
                        delivered_quantity=int(row["delivered_quantity"]),
                        unit_price=float(row["unit_price"]),
                        status="pending" if row["delivered_quantity"] == 0 else "partial",
                        notes=f"Imported from Excel file: {filename}"
                    )
                    customer_requirements.append(req_data)
            
            return {
                "success": True,
                "total_rows": len(df),
                "valid_rows": len(valid_rows),
                "error_rows": len(errors),
                "errors": errors,
                "customer_requirements": customer_requirements,
                "summary": {
                    "total_po_quantity": df["po_quantity"].sum(),
                    "total_delivered": df["delivered_quantity"].sum(),
                    "total_value": df["total_value"].sum(),
                    "shortage_count": len(df[df["shortage_surplus"] < 0]),
                    "complete_count": len(df[df["shortage_surplus"] >= 0])
                }
            }
            
        except Exception as e:
            raise ExcelProcessingError(f"Failed to process Excel file: {str(e)}")
    
    async def process_product_upload(
        self, 
        file: BinaryIO, 
        filename: str,
        validate_only: bool = False
    ) -> Dict[str, Any]:
        """
        Process uploaded Excel file containing product data.
        
        Args:
            file: Excel file binary data
            filename: Original filename
            validate_only: If True, only validate data without processing
            
        Returns:
            Dict containing processing results and any errors
        """
        try:
            # Read Excel file
            df = pd.read_excel(file, sheet_name=0)
            
            # Validate required columns
            required_columns = [
                "part_no", "part_name", "material_code", 
                "material_description", "unit_of_measure", "standard_cost"
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ExcelProcessingError(f"Missing required columns: {missing_columns}")
            
            # Clean and validate data
            df = df.dropna(subset=["part_no", "part_name"])
            
            # Convert data types
            df["standard_cost"] = pd.to_numeric(df["standard_cost"], errors="coerce")
            df["unit_of_measure"] = df["unit_of_measure"].fillna("PCS")
            
            # Validate data
            errors = []
            valid_rows = []
            
            for index, row in df.iterrows():
                row_errors = []
                
                # Validate required fields
                if not row["part_no"] or len(str(row["part_no"])) == 0:
                    row_errors.append("Part number is required")
                if not row["part_name"] or len(str(row["part_name"])) == 0:
                    row_errors.append("Part name is required")
                if pd.isna(row["standard_cost"]) or row["standard_cost"] < 0:
                    row_errors.append("Invalid standard_cost")
                
                if row_errors:
                    errors.append({
                        "row": index + 2,
                        "part_no": row["part_no"],
                        "errors": row_errors
                    })
                else:
                    valid_rows.append(row)
            
            # Create ProductCreate objects
            products = []
            if not validate_only:
                for row in valid_rows:
                    product_data = ProductCreate(
                        part_no=str(row["part_no"]),
                        part_name=str(row["part_name"]),
                        drawing_no=str(row.get("drawing_no", "")),
                        material_code=str(row.get("material_code", "")),
                        material_description=str(row.get("material_description", "")),
                        unit_of_measure=str(row["unit_of_measure"]),
                        standard_cost=float(row["standard_cost"]),
                        specifications={}
                    )
                    products.append(product_data)
            
            return {
                "success": True,
                "total_rows": len(df),
                "valid_rows": len(valid_rows),
                "error_rows": len(errors),
                "errors": errors,
                "products": products
            }
            
        except Exception as e:
            raise ExcelProcessingError(f"Failed to process product file: {str(e)}")
    
    async def export_customer_requirements(
        self, 
        requirements: List[Dict[str, Any]],
        include_formulas: bool = True
    ) -> bytes:
        """
        Export customer requirements to Excel with formatting.
        
        Args:
            requirements: List of customer requirement data
            include_formulas: Whether to include Excel formulas
            
        Returns:
            Excel file as bytes
        """
        try:
            # Create DataFrame
            df = pd.DataFrame(requirements)
            
            # Create workbook and worksheet
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Customer Requirements"
            
            # Define columns
            columns = [
                "Sale No", "PO No", "Customer Name", "Product Part No", 
                "Product Name", "Due Date", "PO Quantity", "Delivered Quantity",
                "Shortage/Surplus", "Summary Status", "Unit Price", "Total Value", "Status"
            ]
            
            # Add headers
            for col_num, column_title in enumerate(columns, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = column_title
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.border = self.border
                cell.alignment = self.center_alignment
            
            # Add data
            for row_num, req in enumerate(requirements, 2):
                ws.cell(row=row_num, column=1, value=req.get("sale_no"))
                ws.cell(row=row_num, column=2, value=req.get("po_no"))
                ws.cell(row=row_num, column=3, value=req.get("customer_name"))
                ws.cell(row=row_num, column=4, value=req.get("product_part_no"))
                ws.cell(row=row_num, column=5, value=req.get("product_part_name"))
                ws.cell(row=row_num, column=6, value=req.get("due_date"))
                ws.cell(row=row_num, column=7, value=req.get("po_quantity"))
                ws.cell(row=row_num, column=8, value=req.get("delivered_quantity"))
                
                # Add formulas if requested
                if include_formulas:
                    # Shortage/Surplus formula (Delivered - PO)
                    shortage_cell = ws.cell(row=row_num, column=9)
                    shortage_cell.value = f"=H{row_num}-G{row_num}"
                    
                    # Summary Status formula
                    status_cell = ws.cell(row=row_num, column=10)
                    status_cell.value = f'=IF(I{row_num}>=0,"Complete","Shortage")'
                    
                    # Total Value formula
                    total_cell = ws.cell(row=row_num, column=12)
                    total_cell.value = f"=G{row_num}*K{row_num}"
                else:
                    ws.cell(row=row_num, column=9, value=req.get("shortage_surplus"))
                    ws.cell(row=row_num, column=10, value=req.get("summary_status"))
                    ws.cell(row=row_num, column=12, value=req.get("total_value"))
                
                ws.cell(row=row_num, column=11, value=req.get("unit_price"))
                ws.cell(row=row_num, column=13, value=req.get("status"))
                
                # Apply conditional formatting for status
                status = req.get("summary_status", "").lower()
                if status in self.status_colors:
                    fill = PatternFill(
                        start_color=self.status_colors[status],
                        end_color=self.status_colors[status],
                        fill_type="solid"
                    )
                    ws.cell(row=row_num, column=10).fill = fill
            
            # Apply borders to all cells
            for row in ws.iter_rows():
                for cell in row:
                    cell.border = self.border
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Add data validation for status columns
            status_validation = DataValidation(
                type="list",
                formula1='"pending,partial,completed,cancelled"',
                allow_blank=False
            )
            ws.add_data_validation(status_validation)
            status_validation.add(f"M2:M{len(requirements) + 1}")
            
            # Add totals row
            total_row = len(requirements) + 3
            ws.cell(row=total_row, column=6, value="TOTALS:").font = Font(bold=True)
            ws.cell(row=total_row, column=7, value=f"=SUM(G2:G{len(requirements) + 1})")
            ws.cell(row=total_row, column=8, value=f"=SUM(H2:H{len(requirements) + 1})")
            ws.cell(row=total_row, column=12, value=f"=SUM(L2:L{len(requirements) + 1})")
            
            # Save to bytes
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            raise ExcelProcessingError(f"Failed to export customer requirements: {str(e)}")
    
    async def export_production_orders(
        self, 
        orders: List[Dict[str, Any]]
    ) -> bytes:
        """
        Export production orders to Excel with formatting.
        
        Args:
            orders: List of production order data
            
        Returns:
            Excel file as bytes
        """
        try:
            # Create DataFrame
            df = pd.DataFrame(orders)
            
            # Create workbook and worksheet
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Production Orders"
            
            # Define columns
            columns = [
                "Production Order No", "Customer Name", "Product Part No", 
                "Product Name", "Planned Quantity", "Produced Quantity",
                "Completion %", "Target Date", "Status", "Priority", "Assigned To"
            ]
            
            # Add headers
            for col_num, column_title in enumerate(columns, 1):
                cell = ws.cell(row=1, column=col_num)
                cell.value = column_title
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.border = self.border
                cell.alignment = self.center_alignment
            
            # Add data
            for row_num, order in enumerate(orders, 2):
                ws.cell(row=row_num, column=1, value=order.get("production_order_no"))
                ws.cell(row=row_num, column=2, value=order.get("customer_name"))
                ws.cell(row=row_num, column=3, value=order.get("product_part_no"))
                ws.cell(row=row_num, column=4, value=order.get("product_part_name"))
                ws.cell(row=row_num, column=5, value=order.get("planned_quantity"))
                ws.cell(row=row_num, column=6, value=order.get("produced_quantity"))
                
                # Completion percentage formula
                completion_cell = ws.cell(row=row_num, column=7)
                completion_cell.value = f"=IF(E{row_num}>0,F{row_num}/E{row_num}*100,0)"
                completion_cell.number_format = "0.0%"
                
                ws.cell(row=row_num, column=8, value=order.get("target_completion_date"))
                ws.cell(row=row_num, column=9, value=order.get("production_status"))
                ws.cell(row=row_num, column=10, value=order.get("priority"))
                ws.cell(row=row_num, column=11, value=order.get("assigned_to_name"))
                
                # Apply conditional formatting for completion percentage
                completion_pct = order.get("completion_percentage", 0)
                if completion_pct >= 100:
                    fill_color = "90EE90"  # Light green
                elif completion_pct >= 75:
                    fill_color = "FFE4B5"  # Moccasin
                elif completion_pct >= 50:
                    fill_color = "FFA500"  # Orange
                else:
                    fill_color = "FFB6C1"  # Light pink
                
                completion_cell.fill = PatternFill(
                    start_color=fill_color,
                    end_color=fill_color,
                    fill_type="solid"
                )
            
            # Apply borders and auto-adjust columns
            for row in ws.iter_rows():
                for cell in row:
                    cell.border = self.border
            
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Add data bar for completion percentage
            data_bar_rule = DataBarRule(
                start_type="min", start_value=0,
                end_type="max", end_value=100,
                color="4F81BD"
            )
            ws.conditional_formatting.add(f"G2:G{len(orders) + 1}", data_bar_rule)
            
            # Save to bytes
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            raise ExcelProcessingError(f"Failed to export production orders: {str(e)}")
    
    async def create_vlookup_template(self) -> bytes:
        """
        Create Excel template with VLOOKUP formulas for product information.
        
        Returns:
            Excel template file as bytes
        """
        try:
            wb = openpyxl.Workbook()
            
            # Create Product Master sheet
            product_sheet = wb.active
            product_sheet.title = "Product Master"
            
            # Product Master headers
            product_headers = [
                "Part No", "Part Name", "Drawing No", "Material Code", 
                "Material Description", "Unit of Measure", "Standard Cost"
            ]
            
            for col_num, header in enumerate(product_headers, 1):
                cell = product_sheet.cell(row=1, column=col_num)
                cell.value = header
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.border = self.border
            
            # Add sample product data
            sample_products = [
                ["PART001", "Sample Part 1", "DRW001", "MAT001", "Steel Rod 10mm", "PCS", 25.50],
                ["PART002", "Sample Part 2", "DRW002", "MAT002", "Aluminum Sheet", "SQM", 45.75],
                ["PART003", "Sample Part 3", "DRW003", "MAT003", "Copper Wire", "MTR", 12.30],
            ]
            
            for row_num, product in enumerate(sample_products, 2):
                for col_num, value in enumerate(product, 1):
                    product_sheet.cell(row=row_num, column=col_num, value=value)
            
            # Create Customer Requirements sheet with VLOOKUP formulas
            req_sheet = wb.create_sheet("Customer Requirements")
            
            # Customer Requirements headers
            req_headers = [
                "Sale No", "PO No", "Customer Name", "Product Part No",
                "Product Name", "Unit Price", "PO Quantity", "Delivered Quantity",
                "Shortage/Surplus", "Summary Status", "Total Value"
            ]
            
            for col_num, header in enumerate(req_headers, 1):
                cell = req_sheet.cell(row=1, column=col_num)
                cell.value = header
                cell.font = self.header_font
                cell.fill = self.header_fill
                cell.border = self.border
            
            # Add sample data with VLOOKUP formulas
            sample_row = 2
            req_sheet.cell(row=sample_row, column=1, value="SALE001")
            req_sheet.cell(row=sample_row, column=2, value="PO001")
            req_sheet.cell(row=sample_row, column=3, value="Sample Customer")
            req_sheet.cell(row=sample_row, column=4, value="PART001")
            
            # VLOOKUP formula for Product Name
            product_name_cell = req_sheet.cell(row=sample_row, column=5)
            product_name_cell.value = f'=VLOOKUP(D{sample_row},\'Product Master\'.$A:$G,2,FALSE)'
            
            # VLOOKUP formula for Unit Price (using Standard Cost)
            unit_price_cell = req_sheet.cell(row=sample_row, column=6)
            unit_price_cell.value = f'=VLOOKUP(D{sample_row},\'Product Master\'.$A:$G,7,FALSE)'
            
            req_sheet.cell(row=sample_row, column=7, value=100)  # PO Quantity
            req_sheet.cell(row=sample_row, column=8, value=75)   # Delivered Quantity
            
            # Shortage/Surplus formula
            shortage_cell = req_sheet.cell(row=sample_row, column=9)
            shortage_cell.value = f"=H{sample_row}-G{sample_row}"
            
            # Summary Status formula
            status_cell = req_sheet.cell(row=sample_row, column=10)
            status_cell.value = f'=IF(I{sample_row}>=0,"Complete","Shortage")'
            
            # Total Value formula
            total_cell = req_sheet.cell(row=sample_row, column=11)
            total_cell.value = f"=F{sample_row}*G{sample_row}"
            
            # Auto-adjust column widths for both sheets
            for sheet in [product_sheet, req_sheet]:
                for column in sheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    sheet.column_dimensions[column_letter].width = adjusted_width
            
            # Save to bytes
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            raise ExcelProcessingError(f"Failed to create VLOOKUP template: {str(e)}")


# Global service instance
excel_service = ExcelService()