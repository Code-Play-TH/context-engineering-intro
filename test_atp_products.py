#!/usr/bin/env python3
"""
Test script for ATP Product Excel import functionality.

Tests the ATP Product import service with actual Excel data.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.atp_product_import import atp_product_import_service


async def test_atp_product_processing():
    """Test ATP Product Excel file processing."""
    print("=== ATP Product Excel Import Test ===\n")
    
    try:
        # Test file processing
        excel_file_path = "examples/Product Info Database.xlsx"
        print(f"Processing Excel file: {excel_file_path}")
        
        if not os.path.exists(excel_file_path):
            print(f"❌ Excel file not found: {excel_file_path}")
            return False
            
        processing_result = atp_product_import_service.process_excel_file(excel_file_path)
        
        print(f"✅ File processed successfully!")
        print(f"   Products found: {processing_result.products_found}")
        
        if processing_result.processing_errors:
            print(f"⚠️  Processing errors: {len(processing_result.processing_errors)}")
            for error in processing_result.processing_errors:
                print(f"   - {error}")
        else:
            print(f"✅ No processing errors")
        
        # Show sample products
        print(f"\n=== Sample Products (first 5) ===")
        for i, product in enumerate(processing_result.products[:5]):
            print(f"{i+1}. Part No: {product.part_no}")
            print(f"   Drawing No: {product.drawing_no}")
            print(f"   Part Name: {product.part_name}")
            print(f"   Material Code: {product.material_code}")
            print(f"   Material Description (TH): {product.material_description_th}")
            print(f"   Total Steps: {product.total_steps}")
            print(f"   Turning Steps: {product.turning_steps}")
            print(f"   Milling Steps: {product.milling_steps}")
            print(f"   Color: {product.color_description}")
            
            if product.process_steps:
                steps = ", ".join([f"{k}:{v}" for k, v in list(product.process_steps.items())[:3]])
                print(f"   Process Steps: {steps}...")
            print("")
        
        # Show statistics by complexity
        complexity_stats = {}
        color_stats = {}
        material_stats = {}
        
        for product in processing_result.products:
            # Calculate complexity
            if product.total_steps:
                if product.total_steps <= 2:
                    complexity = "Simple"
                elif product.total_steps <= 5:
                    complexity = "Medium"  
                else:
                    complexity = "Complex"
                complexity_stats[complexity] = complexity_stats.get(complexity, 0) + 1
            
            # Count colors
            if product.color_code:
                color_stats[product.color_code] = color_stats.get(product.color_code, 0) + 1
            
            # Count materials
            if product.material_code:
                material_stats[product.material_code] = material_stats.get(product.material_code, 0) + 1
        
        print(f"=== Product Statistics ===")
        print(f"Total Products: {processing_result.products_found}")
        print(f"Products with Material Code: {sum(1 for p in processing_result.products if p.material_code)}")
        print(f"Products with Process Steps: {sum(1 for p in processing_result.products if p.process_steps)}")
        print(f"Products with Color Info: {sum(1 for p in processing_result.products if p.color_code)}")
        
        print(f"\nComplexity Breakdown:")
        for complexity, count in sorted(complexity_stats.items()):
            print(f"  {complexity}: {count}")
        
        print(f"\nTop 5 Material Codes:")
        top_materials = sorted(material_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        for material, count in top_materials:
            print(f"  {material}: {count}")
        
        print(f"\nColor Codes Found:")
        for color, count in sorted(color_stats.items()):
            print(f"  {color}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    print("Starting ATP Product Excel import test...\n")
    
    # Run the async test
    result = asyncio.run(test_atp_product_processing())
    
    if result:
        print("\n✅ ATP Product Excel import test completed successfully!")
        print("The system can now import your complete product database!")
    else:
        print("\n❌ ATP Product Excel import test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()