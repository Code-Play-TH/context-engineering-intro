"""
ATP Product Excel import service.

Handles importing products from the Product Info Database sheet with proper
material code relationships and production process data.
"""

import pandas as pd
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.atp_product import ATPProduct, ATPProductionStep
from app.models.atp_master_data import ATPMaterialCode
from app.schemas.atp_product import (
    ATPProductExcelImport,
    ATPProductImportResponse,
    ATPProductProcessingResult
)


class ATPProductImportService:
    """Service for importing ATP Product data from Excel."""
    
    def __init__(self):
        """Initialize the service."""
        self.color_patterns = {
            'MATT BLACK': ('0', 'MATT BLACK', 'ดำด้าน'),
            'BLACK': ('8', 'BLACK', 'ดำ'),
            'WHITE': ('2', 'WHITE', 'ขาว'),
            'RED': ('5', 'RED', 'แดง'),
            'BLUE': ('6', 'BLUE', 'น้ำเงิน'),
            'CHROME': ('1', 'CHROME', 'โครม'),
            'GOLD': ('3', 'GOLD', 'ทอง'),
            'YELLOW': ('4', 'YELLOW', 'เหลือง'),
            'ORANGE': ('7', 'ORANGE', 'ส้ม'),
            'HT': ('9', 'HT', 'HT'),
        }
    
    def process_excel_file(self, file_path: str) -> ATPProductProcessingResult:
        """
        Process ATP Product Excel file and extract product data.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            ATPProductProcessingResult: Processed data and any errors
        """
        result = ATPProductProcessingResult(
            products_found=0,
            products=[],
            processing_errors=[]
        )
        
        try:
            # Process Product Info Database sheet
            df = pd.read_excel(file_path, sheet_name='Product Info Database')
            products = self._process_products(df)
            result.products = products
            result.products_found = len(products)
            
        except Exception as e:
            result.processing_errors.append(f"Excel file processing error: {str(e)}")
        
        return result
    
    def _process_products(self, df: pd.DataFrame) -> List[ATPProductExcelImport]:
        """Process Product Info Database sheet data."""
        products = []
        
        # Clean the dataframe - keep products with Part No
        df_clean = df.dropna(subset=['Part No'])
        
        for _, row in df_clean.iterrows():
            try:
                # Extract basic product info
                part_no = str(row['Part No']).strip()
                if not part_no or part_no == 'nan':
                    continue
                
                # Extract process steps (P1-P15)
                process_steps = {}
                for i in range(1, 16):
                    col = f'P{i}'
                    if col in df.columns and pd.notna(row.get(col)):
                        process_steps[col] = str(row[col]).strip()
                
                # Extract color information from part name
                color_code, color_description = self._extract_color_from_name(
                    str(row.get('Part Name', ''))
                )
                
                # Convert numeric fields safely
                total_steps = self._safe_float_convert(row.get('ขั้นตอนทั้งหมด'))
                turning_steps = self._safe_float_convert(
                    row.get('ขั้นตอน\nงานกลึง')
                )
                cuts_per_box = self._safe_float_convert(row.get('จำนวนตัด/ลัง'))
                
                # Get milling steps (might be text)
                milling_steps = None
                milling_col = 'ขั้นตอน\nงานกัด'
                if milling_col in df.columns and pd.notna(row.get(milling_col)):
                    milling_steps = str(row[milling_col]).strip()
                
                # Create product import object
                product = ATPProductExcelImport(
                    part_no=part_no,
                    drawing_no=self._safe_str_convert(row.get('Drawing No')),
                    revision=self._safe_str_convert(row.get('Revision')),
                    part_name=self._safe_str_convert(row.get('Part Name')),
                    material_code=self._safe_str_convert(row.get('Material Code')),
                    material_description_th=self._safe_str_convert(
                        row.get('รายละเอียดวัตถุดิบ')
                    ),
                    material_length=self._safe_str_convert(row.get('ความยาววัตถุดิบ')),
                    cuts_per_box=cuts_per_box,
                    total_steps=total_steps,
                    turning_steps=turning_steps,
                    milling_steps=milling_steps,
                    color_code=color_code,
                    color_description=color_description,
                    process_steps=process_steps
                )
                
                products.append(product)
                
            except Exception as e:
                # Skip invalid rows but continue processing
                continue
        
        return products
    
    def _extract_color_from_name(self, part_name: str) -> tuple[Optional[str], Optional[str]]:
        """
        Extract color information from part name.
        
        Args:
            part_name: Product part name
            
        Returns:
            tuple: (color_code, color_description) or (None, None)
        """
        if not part_name:
            return None, None
            
        name_upper = part_name.upper()
        
        for color_name, (code, desc_en, desc_th) in self.color_patterns.items():
            if color_name in name_upper:
                return code, f"{desc_en}({desc_th})"
        
        return None, None
    
    def _safe_str_convert(self, value: Any) -> Optional[str]:
        """Safely convert value to string."""
        if pd.isna(value) or value is None:
            return None
        str_val = str(value).strip()
        return str_val if str_val and str_val != 'nan' else None
    
    def _safe_float_convert(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if pd.isna(value) or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    async def import_products(
        self, 
        products: List[ATPProductExcelImport],
        db: AsyncSession,
        update_existing: bool = False
    ) -> ATPProductImportResponse:
        """Import ATP products to database."""
        total_processed = len(products)
        created = 0
        updated = 0
        errors = []
        
        # Get material code mapping for lookups
        material_code_map = await self._get_material_code_mapping(db)
        
        for i, product_data in enumerate(products):
            try:
                # Check if exists by part number
                existing = await db.execute(
                    select(ATPProduct).where(ATPProduct.part_no == product_data.part_no)
                )
                existing_product = existing.scalar_one_or_none()
                
                if existing_product:
                    if update_existing:
                        # Update existing product
                        await self._update_product(
                            existing_product, product_data, material_code_map, db
                        )
                        updated += 1
                    else:
                        errors.append({
                            "row": i + 1,
                            "part_no": product_data.part_no,
                            "error": "Product already exists"
                        })
                else:
                    # Create new product
                    new_product = await self._create_product(
                        product_data, material_code_map, db
                    )
                    db.add(new_product)
                    created += 1
                    
            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "part_no": product_data.part_no,
                    "error": str(e)
                })
        
        await db.commit()
        
        success_rate = ((created + updated) / total_processed) * 100 if total_processed > 0 else 0
        
        return ATPProductImportResponse(
            total_processed=total_processed,
            created=created,
            updated=updated,
            errors=errors,
            success_rate=success_rate
        )
    
    async def _get_material_code_mapping(self, db: AsyncSession) -> Dict[str, int]:
        """Get mapping of material codes to IDs."""
        result = await db.execute(select(ATPMaterialCode))
        materials = result.scalars().all()
        return {mat.material_code: mat.id for mat in materials}
    
    async def _create_product(
        self,
        product_data: ATPProductExcelImport,
        material_code_map: Dict[str, int],
        db: AsyncSession
    ) -> ATPProduct:
        """Create new ATP product."""
        # Get material code ID if exists
        atp_material_code_id = None
        if product_data.material_code:
            atp_material_code_id = material_code_map.get(product_data.material_code)
        
        # Create product
        product = ATPProduct(
            part_no=product_data.part_no,
            drawing_no=product_data.drawing_no,
            revision=product_data.revision,
            part_name=product_data.part_name,
            material_code=product_data.material_code,
            atp_material_code_id=atp_material_code_id,
            material_description_th=product_data.material_description_th,
            material_length=product_data.material_length,
            cuts_per_box=product_data.cuts_per_box,
            total_steps=product_data.total_steps,
            turning_steps=product_data.turning_steps,
            milling_steps=product_data.milling_steps,
            color_code=product_data.color_code,
            color_description=product_data.color_description,
            process_steps_json=pd.io.json.dumps(product_data.process_steps) if product_data.process_steps else None
        )
        
        # Set complexity level
        product.update_complexity_level()
        
        # Create production steps if available
        if product_data.process_steps:
            await self._create_production_steps(product, product_data.process_steps, db)
        
        return product
    
    async def _update_product(
        self,
        existing_product: ATPProduct,
        product_data: ATPProductExcelImport,
        material_code_map: Dict[str, int],
        db: AsyncSession
    ) -> None:
        """Update existing ATP product."""
        # Update basic fields
        existing_product.drawing_no = product_data.drawing_no
        existing_product.revision = product_data.revision
        existing_product.part_name = product_data.part_name
        existing_product.material_code = product_data.material_code
        existing_product.material_description_th = product_data.material_description_th
        existing_product.material_length = product_data.material_length
        existing_product.cuts_per_box = product_data.cuts_per_box
        existing_product.total_steps = product_data.total_steps
        existing_product.turning_steps = product_data.turning_steps
        existing_product.milling_steps = product_data.milling_steps
        existing_product.color_code = product_data.color_code
        existing_product.color_description = product_data.color_description
        
        # Update material code relationship
        if product_data.material_code:
            existing_product.atp_material_code_id = material_code_map.get(product_data.material_code)
        
        # Update process steps
        if product_data.process_steps:
            existing_product.process_steps_json = pd.io.json.dumps(product_data.process_steps)
            
            # Update production steps (remove old, add new)
            for step in existing_product.production_steps:
                await db.delete(step)
            
            await self._create_production_steps(existing_product, product_data.process_steps, db)
        
        # Update complexity level
        existing_product.update_complexity_level()
        existing_product.touch()
    
    async def _create_production_steps(
        self,
        product: ATPProduct,
        process_steps: Dict[str, str],
        db: AsyncSession
    ) -> None:
        """Create production steps for product."""
        for step_name, step_code in process_steps.items():
            # Extract step number from P1, P2, etc.
            step_match = re.match(r'P(\d+)', step_name)
            if step_match:
                step_number = int(step_match.group(1))
                
                # Determine step type from code
                step_type = self._determine_step_type(step_code)
                
                step = ATPProductionStep(
                    atp_product_id=product.id,
                    step_number=step_number,
                    step_code=step_code,
                    step_type=step_type,
                    step_description=f"Step {step_number}: {step_code}"
                )
                
                db.add(step)
    
    def _determine_step_type(self, step_code: str) -> Optional[str]:
        """
        Determine step type from step code.
        
        Args:
            step_code: Step code (L1, M1, etc.)
            
        Returns:
            Optional[str]: Step type or None
        """
        if not step_code:
            return None
            
        code_upper = step_code.upper()
        
        if code_upper.startswith('L'):
            return 'turning'  # Lathe operations
        elif code_upper.startswith('M'):
            return 'milling'  # Milling operations
        elif code_upper.startswith('D'):
            return 'drilling'
        elif code_upper.startswith('G'):
            return 'grinding'
        else:
            return 'other'


# Global service instance
atp_product_import_service = ATPProductImportService()