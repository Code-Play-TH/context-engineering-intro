#!/usr/bin/env python3
"""
Simple test for ATP Excel processing without database dependencies.
"""

import pandas as pd
import os


def test_excel_processing():
    """Test Excel file processing directly with pandas."""
    print("=== Simple ATP Excel Processing Test ===\n")
    
    try:
        excel_file_path = "examples/Product Info Database.xlsx"
        print(f"Processing Excel file: {excel_file_path}")
        
        if not os.path.exists(excel_file_path):
            print(f"❌ Excel file not found: {excel_file_path}")
            return False
        
        # Process Material Code sheet
        print("\n=== Processing Material Code Sheet ===")
        df_material = pd.read_excel(excel_file_path, sheet_name='Material Code')
        print(f"Material Code sheet shape: {df_material.shape}")
        print(f"Columns: {list(df_material.columns)}")
        
        # Clean and show sample data
        df_material_clean = df_material.dropna(subset=['ATP Code', 'Material Code', 'รายละเอียด'])
        print(f"After cleaning (removing NaN): {df_material_clean.shape[0]} rows")
        
        print(f"\nFirst 5 material codes:")
        for i, (_, row) in enumerate(df_material_clean.head().iterrows()):
            print(f"{i+1}. ATP Code: {row['ATP Code']}")
            print(f"   Material Code: {row['Material Code']}")
            print(f"   Description (TH): {row['รายละเอียด']}")
            print(f"   Grade: {row.get('GRADE', 'N/A')}")
            print(f"   Weight/Line: {row.get('น้ำหนัก/เส้น', 'N/A')}")
            print(f"   Length/Piece: {row.get('ยาว/ท่อน', 'N/A')}")
            print("")
        
        # Process Color Code sheet
        print("=== Processing Color Code Sheet ===")
        df_color = pd.read_excel(excel_file_path, sheet_name='Color Code')
        print(f"Color Code sheet shape: {df_color.shape}")
        print(f"Columns: {list(df_color.columns)}")
        
        # Clean and show sample data
        df_color_clean = df_color.dropna(subset=['Color Code', 'Color'])
        print(f"After cleaning (removing NaN): {df_color_clean.shape[0]} rows")
        
        print(f"\nFirst 10 color codes:")
        for i, (_, row) in enumerate(df_color_clean.head(10).iterrows()):
            print(f"{i+1}. Color Code: {row['Color Code']} -> Color: {row['Color']}")
        
        # Show statistics
        print(f"\n=== Processing Statistics ===")
        print(f"Material Codes found: {len(df_material_clean)}")
        print(f"Color Codes found: {len(df_color_clean)}")
        
        # Test data type conversions
        print(f"\n=== Testing Data Type Conversions ===")
        test_material = df_material_clean.iloc[0]
        
        # Test weight conversion
        weight_per_line = None
        if pd.notna(test_material.get('น้ำหนัก/เส้น')):
            try:
                weight_per_line = float(test_material['น้ำหนัก/เส้น'])
                print(f"✅ Weight conversion successful: {weight_per_line}")
            except (ValueError, TypeError) as e:
                print(f"⚠️  Weight conversion failed: {e}")
        
        # Test length conversion
        length_per_piece = None
        if pd.notna(test_material.get('ยาว/ท่อน')):
            try:
                length_per_piece = float(test_material['ยาว/ท่อน'])
                print(f"✅ Length conversion successful: {length_per_piece}")
            except (ValueError, TypeError) as e:
                print(f"⚠️  Length conversion failed: {e}")
        
        # Test grade processing
        grade = str(test_material.get('GRADE', '')).strip()
        if grade == '-' or grade == '':
            grade = None
        print(f"✅ Grade processing: '{grade}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    print("Starting simple Excel processing test...\n")
    
    result = test_excel_processing()
    
    if result:
        print("\n✅ Excel processing test completed successfully!")
        print("The ATP Excel import service should work correctly.")
    else:
        print("\n❌ Excel processing test failed!")


if __name__ == "__main__":
    main()