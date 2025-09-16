"""
ATP Excel import service for Material Code and Color Code data.

Handles importing data from your actual Excel file structure.
"""

import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.atp_master_data import ATPMaterialCode, ATPColorCode
from app.schemas.atp_master_data import (
    ATPMaterialCodeExcelImport, 
    ATPColorCodeExcelImport,
    ATPExcelProcessingResult,
    ATPMasterDataImportResponse
)


class ATPExcelImportService:
    """Service for importing ATP Excel data."""
    
    def __init__(self):
        """Initialize the service."""
        pass
    
    def process_excel_file(self, file_path: str) -> ATPExcelProcessingResult:
        """
        Process ATP Excel file and extract Material Code and Color Code data.
        
        Args:
            file_path: Path to the Excel file
            
        Returns:
            ATPExcelProcessingResult: Processed data and any errors
        """
        result = ATPExcelProcessingResult(
            material_codes_found=0,
            color_codes_found=0,
            material_codes=[],
            color_codes=[],
            processing_errors=[]
        )
        
        try:
            # Process Material Code sheet
            try:
                df_material = pd.read_excel(file_path, sheet_name='Material Code')
                material_codes = self._process_material_codes(df_material)
                result.material_codes = material_codes
                result.material_codes_found = len(material_codes)
            except Exception as e:
                result.processing_errors.append(f"Material Code sheet error: {str(e)}")
            
            # Process Color Code sheet
            try:
                df_color = pd.read_excel(file_path, sheet_name='Color Code')
                color_codes = self._process_color_codes(df_color)
                result.color_codes = color_codes
                result.color_codes_found = len(color_codes)
            except Exception as e:
                result.processing_errors.append(f"Color Code sheet error: {str(e)}")
            
        except Exception as e:
            result.processing_errors.append(f"Excel file processing error: {str(e)}")
        
        return result
    
    def _process_material_codes(self, df: pd.DataFrame) -> List[ATPMaterialCodeExcelImport]:
        """Process Material Code sheet data."""
        material_codes = []
        
        # Clean the dataframe
        df = df.dropna(subset=['ATP Code', 'Material Code', 'รายละเอียด'])
        
        for _, row in df.iterrows():
            try:
                # Convert data types
                length_per_piece = None
                if pd.notna(row.get('ยาว/ท่อน')):
                    try:
                        length_per_piece = float(row['ยาว/ท่อน'])
                    except (ValueError, TypeError):
                        pass
                
                weight_per_line = None
                if pd.notna(row.get('น้ำหนัก/เส้น')):
                    try:
                        weight_per_line = float(row['น้ำหนัก/เส้น'])
                    except (ValueError, TypeError):
                        pass
                
                grade = str(row.get('GRADE', '')).strip()
                if grade == '-' or grade == '':
                    grade = None
                
                material_code = ATPMaterialCodeExcelImport(
                    atp_code=str(row['ATP Code']).strip(),
                    material_code=str(row['Material Code']).strip(),
                    description_th=str(row['รายละเอียด']).strip(),
                    length_per_piece=length_per_piece,
                    grade=grade,
                    weight_per_line=weight_per_line
                )
                material_codes.append(material_code)
                
            except Exception as e:
                # Skip invalid rows but continue processing
                continue
        
        return material_codes
    
    def _process_color_codes(self, df: pd.DataFrame) -> List[ATPColorCodeExcelImport]:
        """Process Color Code sheet data."""
        color_codes = []
        
        # Clean the dataframe - only process rows with both Color Code and Color
        df_clean = df.dropna(subset=['Color Code', 'Color'])
        
        for _, row in df_clean.iterrows():
            try:
                color_code = ATPColorCodeExcelImport(
                    color_code=str(row['Color Code']).strip(),
                    color_name=str(row['Color']).strip()
                )
                color_codes.append(color_code)
                
            except Exception as e:
                # Skip invalid rows but continue processing
                continue
        
        return color_codes
    
    async def import_material_codes(
        self, 
        material_codes: List[ATPMaterialCodeExcelImport],
        db: AsyncSession,
        update_existing: bool = False
    ) -> ATPMasterDataImportResponse:
        """Import material codes to database."""
        total_processed = len(material_codes)
        created = 0
        updated = 0
        errors = []
        
        for i, material_data in enumerate(material_codes):
            try:
                # Check if exists by ATP code
                existing = await db.execute(
                    select(ATPMaterialCode).where(ATPMaterialCode.atp_code == material_data.atp_code)
                )
                existing_material = existing.scalar_one_or_none()
                
                if existing_material:
                    if update_existing:
                        # Update existing
                        existing_material.material_code = material_data.material_code
                        existing_material.description_th = material_data.description_th
                        existing_material.length_per_piece = material_data.length_per_piece
                        existing_material.grade = material_data.grade
                        existing_material.weight_per_line = material_data.weight_per_line
                        existing_material.touch()
                        updated += 1
                    else:
                        errors.append({
                            "row": i + 1,
                            "atp_code": material_data.atp_code,
                            "error": "Material code already exists"
                        })
                else:
                    # Create new
                    new_material = ATPMaterialCode(
                        atp_code=material_data.atp_code,
                        material_code=material_data.material_code,
                        description_th=material_data.description_th,
                        length_per_piece=material_data.length_per_piece,
                        grade=material_data.grade,
                        weight_per_line=material_data.weight_per_line
                    )
                    db.add(new_material)
                    created += 1
                    
            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "atp_code": material_data.atp_code,
                    "error": str(e)
                })
        
        await db.commit()
        
        success_rate = ((created + updated) / total_processed) * 100 if total_processed > 0 else 0
        
        return ATPMasterDataImportResponse(
            total_processed=total_processed,
            created=created,
            updated=updated,
            errors=errors,
            success_rate=success_rate
        )
    
    async def import_color_codes(
        self, 
        color_codes: List[ATPColorCodeExcelImport],
        db: AsyncSession,
        update_existing: bool = False
    ) -> ATPMasterDataImportResponse:
        """Import color codes to database."""
        total_processed = len(color_codes)
        created = 0
        updated = 0
        errors = []
        
        for i, color_data in enumerate(color_codes):
            try:
                # Check if exists by color code
                existing = await db.execute(
                    select(ATPColorCode).where(ATPColorCode.color_code == color_data.color_code)
                )
                existing_color = existing.scalar_one_or_none()
                
                if existing_color:
                    if update_existing:
                        # Update existing
                        existing_color.color_name = color_data.color_name
                        
                        # Set special properties based on color name
                        if color_data.color_name.upper() in ['RAW', '(RAW)']:
                            existing_color.is_raw_material = True
                            existing_color.color_type = 'Raw Material'
                        elif 'CHROME' in color_data.color_name.upper():
                            existing_color.color_type = 'Chrome Plating'
                            existing_color.process_type = 'Electroplating'
                        elif 'HARD' in color_data.color_name.upper():
                            existing_color.finish_type = 'Hard Anodized'
                            existing_color.process_type = 'Hard Anodizing'
                        elif 'MATT' in color_data.color_name.upper() or 'MATTE' in color_data.color_name.upper():
                            existing_color.finish_type = 'Matte'
                        
                        existing_color.touch()
                        updated += 1
                    else:
                        errors.append({
                            "row": i + 1,
                            "color_code": color_data.color_code,
                            "error": "Color code already exists"
                        })
                else:
                    # Create new
                    new_color = ATPColorCode(
                        color_code=color_data.color_code,
                        color_name=color_data.color_name
                    )
                    
                    # Set special properties based on color name
                    if color_data.color_name.upper() in ['RAW', '(RAW)']:
                        new_color.is_raw_material = True
                        new_color.color_type = 'Raw Material'
                    elif 'CHROME' in color_data.color_name.upper():
                        new_color.color_type = 'Chrome Plating'
                        new_color.process_type = 'Electroplating'
                    elif 'HARD' in color_data.color_name.upper():
                        new_color.finish_type = 'Hard Anodized'
                        new_color.process_type = 'Hard Anodizing'
                    elif 'MATT' in color_data.color_name.upper() or 'MATTE' in color_data.color_name.upper():
                        new_color.finish_type = 'Matte'
                    
                    db.add(new_color)
                    created += 1
                    
            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "color_code": color_data.color_code,
                    "error": str(e)
                })
        
        await db.commit()
        
        success_rate = ((created + updated) / total_processed) * 100 if total_processed > 0 else 0
        
        return ATPMasterDataImportResponse(
            total_processed=total_processed,
            created=created,
            updated=updated,
            errors=errors,
            success_rate=success_rate
        )


# Global service instance
atp_excel_import_service = ATPExcelImportService()