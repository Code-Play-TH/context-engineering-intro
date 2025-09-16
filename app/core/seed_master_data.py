"""
Seed data for Material Code and Color Code master tables.

Contains sample master data based on typical manufacturing requirements.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.master_data import MaterialCode, ColorCode


async def create_sample_material_codes(db: AsyncSession) -> None:
    """Create sample material codes."""
    
    sample_materials = [
        {
            "material_code": "STL001",
            "material_name": "Carbon Steel A36",
            "material_category": "Steel",
            "material_type": "Carbon Steel",
            "density": 7.85,
            "melting_point": 1510,
            "hardness": "HRB 95",
            "standard_thickness": 2.0,
            "unit_weight": 7.85,
            "cost_per_unit": 2.50,
            "primary_supplier": "Steel Dynamics",
            "supplier_code": "A36-2MM",
            "tensile_strength": 400.0,
            "yield_strength": 250.0,
            "surface_finish": "Mill Finish",
            "specifications": "ASTM A36/A36M standard structural steel",
            "handling_notes": "Store in dry conditions to prevent rust"
        },
        {
            "material_code": "ALU001", 
            "material_name": "Aluminum 6061-T6",
            "material_category": "Aluminum",
            "material_type": "Heat Treated",
            "density": 2.70,
            "melting_point": 582,
            "hardness": "HB 95",
            "standard_thickness": 1.5,
            "unit_weight": 2.70,
            "cost_per_unit": 4.20,
            "primary_supplier": "Alcoa",
            "supplier_code": "6061-T6-1.5",
            "tensile_strength": 310.0,
            "yield_strength": 276.0,
            "surface_finish": "Mill Finish",
            "specifications": "ASTM B221 extruded aluminum alloy",
            "handling_notes": "Good machinability and weldability"
        },
        {
            "material_code": "STS001",
            "material_name": "Stainless Steel 304",
            "material_category": "Stainless Steel", 
            "material_type": "Austenitic",
            "density": 8.0,
            "melting_point": 1400,
            "hardness": "HRB 88",
            "standard_thickness": 1.0,
            "unit_weight": 8.0,
            "cost_per_unit": 6.80,
            "primary_supplier": "Outokumpu",
            "supplier_code": "304-1MM",
            "tensile_strength": 515.0,
            "yield_strength": 205.0,
            "surface_finish": "2B",
            "specifications": "ASTM A240/A240M austenitic stainless steel",
            "handling_notes": "Corrosion resistant, food grade"
        },
        {
            "material_code": "PLA001",
            "material_name": "ABS Plastic",
            "material_category": "Plastic",
            "material_type": "Thermoplastic",
            "density": 1.05,
            "melting_point": 220,
            "hardness": "Shore D 80",
            "standard_thickness": 3.0,
            "unit_weight": 1.05,
            "cost_per_unit": 3.20,
            "primary_supplier": "SABIC",
            "supplier_code": "ABS-3MM",
            "tensile_strength": 40.0,
            "yield_strength": 35.0,
            "surface_finish": "Textured",
            "specifications": "High impact strength thermoplastic",
            "handling_notes": "Good dimensional stability"
        },
        {
            "material_code": "COP001",
            "material_name": "Copper C101",
            "material_category": "Copper",
            "material_type": "Pure Copper",
            "density": 8.96,
            "melting_point": 1083,
            "hardness": "HB 45",
            "standard_thickness": 0.8,
            "unit_weight": 8.96,
            "cost_per_unit": 8.50,
            "primary_supplier": "Aurubis",
            "supplier_code": "C101-0.8",
            "tensile_strength": 220.0,
            "yield_strength": 70.0,
            "surface_finish": "Bright",
            "specifications": "99.9% pure oxygen-free copper",
            "handling_notes": "Excellent electrical conductivity"
        }
    ]
    
    for material_data in sample_materials:
        # Check if already exists
        existing = await db.execute(
            select(MaterialCode).where(MaterialCode.material_code == material_data["material_code"])
        )
        if not existing.scalar_one_or_none():
            material = MaterialCode(**material_data)
            db.add(material)
    
    await db.commit()


async def create_sample_color_codes(db: AsyncSession) -> None:
    """Create sample color codes."""
    
    sample_colors = [
        {
            "color_code": "RED001",
            "color_name": "Safety Red",
            "hex_value": "#FF0000",
            "rgb_value": "255,0,0",
            "cmyk_value": "0,100,100,0",
            "pantone_code": "185 C",
            "ral_code": "RAL 3020",
            "ncs_code": "S 1080-Y90R",
            "color_family": "Red",
            "color_intensity": "High",
            "finish_type": "Gloss",
            "paint_type": "Polyurethane",
            "cure_temperature": 80.0,
            "cure_time_minutes": 30,
            "cost_per_liter": 45.0,
            "coverage_per_liter": 12.0,
            "supplier_name": "PPG Industries",
            "supplier_product_code": "PPG-RED-001",
            "color_tolerance": "Delta E < 1.0",
            "uv_resistance": "Excellent",
            "weather_resistance": "10+ years",
            "application_notes": "Use for safety equipment and warning signs"
        },
        {
            "color_code": "BLU001",
            "color_name": "Corporate Blue",
            "hex_value": "#003366",
            "rgb_value": "0,51,102",
            "cmyk_value": "100,50,0,60",
            "pantone_code": "533 C",
            "ral_code": "RAL 5003",
            "ncs_code": "S 4055-R95B",
            "color_family": "Blue",
            "color_intensity": "Dark",
            "finish_type": "Semi-Gloss",
            "paint_type": "Acrylic",
            "cure_temperature": 60.0,
            "cure_time_minutes": 45,
            "cost_per_liter": 38.0,
            "coverage_per_liter": 14.0,
            "supplier_name": "Sherwin-Williams",
            "supplier_product_code": "SW-BLU-001",
            "color_tolerance": "Delta E < 1.5",
            "uv_resistance": "Good",
            "weather_resistance": "7-10 years",
            "application_notes": "Professional equipment and corporate branding"
        },
        {
            "color_code": "GRN001",
            "color_name": "Machine Green",
            "hex_value": "#228B22",
            "rgb_value": "34,139,34",
            "cmyk_value": "75,0,75,45",
            "pantone_code": "348 C",
            "ral_code": "RAL 6001",
            "ncs_code": "S 3060-G10Y",
            "color_family": "Green",
            "color_intensity": "Medium",
            "finish_type": "Satin",
            "paint_type": "Epoxy",
            "cure_temperature": 120.0,
            "cure_time_minutes": 60,
            "cost_per_liter": 52.0,
            "coverage_per_liter": 10.0,
            "supplier_name": "AkzoNobel",
            "supplier_product_code": "AN-GRN-001",
            "color_tolerance": "Delta E < 2.0",
            "uv_resistance": "Fair",
            "weather_resistance": "5-7 years",
            "application_notes": "Industrial machinery and equipment"
        },
        {
            "color_code": "YEL001",
            "color_name": "Warning Yellow",
            "hex_value": "#FFFF00",
            "rgb_value": "255,255,0",
            "cmyk_value": "0,0,100,0",
            "pantone_code": "Process Yellow",
            "ral_code": "RAL 1023",
            "ncs_code": "S 0580-G90Y",
            "color_family": "Yellow",
            "color_intensity": "High",
            "finish_type": "Gloss",
            "paint_type": "Alkyd",
            "cure_temperature": 70.0,
            "cure_time_minutes": 40,
            "cost_per_liter": 42.0,
            "coverage_per_liter": 13.0,
            "supplier_name": "Benjamin Moore",
            "supplier_product_code": "BM-YEL-001",
            "color_tolerance": "Delta E < 1.0",
            "uv_resistance": "Good",
            "weather_resistance": "8-10 years",
            "application_notes": "Safety barriers and warning equipment"
        },
        {
            "color_code": "BLK001",
            "color_name": "Matte Black",
            "hex_value": "#000000",
            "rgb_value": "0,0,0",
            "cmyk_value": "0,0,0,100",
            "pantone_code": "Process Black",
            "ral_code": "RAL 9005",
            "ncs_code": "S 9000-N",
            "color_family": "Black",
            "color_intensity": "Full",
            "finish_type": "Matte",
            "paint_type": "Powder Coat",
            "cure_temperature": 200.0,
            "cure_time_minutes": 20,
            "cost_per_liter": 35.0,
            "coverage_per_liter": 8.0,
            "supplier_name": "Tiger Drylac",
            "supplier_product_code": "TD-BLK-001",
            "color_tolerance": "Delta E < 0.5",
            "uv_resistance": "Excellent",
            "weather_resistance": "15+ years",
            "application_notes": "Electronics housings and precision equipment"
        },
        {
            "color_code": "WHT001",
            "color_name": "Pure White",
            "hex_value": "#FFFFFF",
            "rgb_value": "255,255,255",
            "cmyk_value": "0,0,0,0",
            "pantone_code": "White",
            "ral_code": "RAL 9003",
            "ncs_code": "S 0500-N",
            "color_family": "White",
            "color_intensity": "Full",
            "finish_type": "Semi-Gloss",
            "paint_type": "Latex",
            "cure_temperature": 25.0,
            "cure_time_minutes": 120,
            "cost_per_liter": 28.0,
            "coverage_per_liter": 16.0,
            "supplier_name": "Dulux",
            "supplier_product_code": "DX-WHT-001",
            "color_tolerance": "Delta E < 1.0",
            "uv_resistance": "Good",
            "weather_resistance": "5-8 years",
            "application_notes": "Clean room equipment and food processing"
        }
    ]
    
    for color_data in sample_colors:
        # Check if already exists
        existing = await db.execute(
            select(ColorCode).where(ColorCode.color_code == color_data["color_code"])
        )
        if not existing.scalar_one_or_none():
            color = ColorCode(**color_data)
            db.add(color)
    
    await db.commit()


async def seed_master_data(db: AsyncSession) -> None:
    """Seed all master data."""
    await create_sample_material_codes(db)
    await create_sample_color_codes(db)