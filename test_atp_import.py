#!/usr/bin/env python3
"""
Test script for ATP Excel import functionality.

Tests the ATP Excel import service without requiring the full web server.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.atp_excel_import import atp_excel_import_service


async def test_atp_excel_processing():
    """Test ATP Excel file processing."""
    print("=== ATP Excel Import Test ===\n")
    
    try:
        # Test file processing
        excel_file_path = "examples/Product Info Database.xlsx"
        print(f"Processing Excel file: {excel_file_path}")
        
        if not os.path.exists(excel_file_path):
            print(f"❌ Excel file not found: {excel_file_path}")
            return False
            
        processing_result = atp_excel_import_service.process_excel_file(excel_file_path)
        
        print(f"✅ File processed successfully!")
        print(f"   Material codes found: {processing_result.material_codes_found}")
        print(f"   Color codes found: {processing_result.color_codes_found}")
        
        if processing_result.processing_errors:
            print(f"⚠️  Processing errors: {len(processing_result.processing_errors)}")
            for error in processing_result.processing_errors:
                print(f"   - {error}")
        else:
            print(f"✅ No processing errors")
        
        # Show sample material codes
        print(f"\n=== Sample Material Codes (first 5) ===")
        for i, material in enumerate(processing_result.material_codes[:5]):
            print(f"{i+1}. ATP Code: {material.atp_code}")
            print(f"   Material Code: {material.material_code}")
            print(f"   Description (TH): {material.description_th}")
            print(f"   Grade: {material.grade}")
            print(f"   Weight/Line: {material.weight_per_line}")
            print(f"   Length/Piece: {material.length_per_piece}")
            print("")
        
        # Show sample color codes
        print(f"=== Sample Color Codes (first 5) ===")
        for i, color in enumerate(processing_result.color_codes[:5]):
            print(f"{i+1}. Color Code: {color.color_code}")
            print(f"   Color Name: {color.color_name}")
            print("")
        
        # Show total stats
        print(f"=== Import Statistics ===")
        print(f"Total Material Codes: {processing_result.material_codes_found}")
        print(f"Total Color Codes: {processing_result.color_codes_found}")
        print(f"Processing Errors: {len(processing_result.processing_errors)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    print("Starting ATP Excel import test...\n")
    
    # Run the async test
    result = asyncio.run(test_atp_excel_processing())
    
    if result:
        print("\n✅ ATP Excel import test completed successfully!")
    else:
        print("\n❌ ATP Excel import test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()