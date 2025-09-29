const XLSX = require('xlsx');
const fs = require('fs-extra');
const path = require('path');

async function convertExcelToCSV() {
  try {
    console.log('🔄 Starting Excel to CSV conversion...');

    // Read the Excel file
    const excelFilePath = path.join(__dirname, '..', 'examples', '[TPM SHOPPING LIST 2025] RATE CARD KOLS&INFLUENCERS.xlsx');

    if (!fs.existsSync(excelFilePath)) {
      throw new Error(`Excel file not found: ${excelFilePath}`);
    }

    console.log('📁 Reading Excel file:', excelFilePath);
    const workbook = XLSX.readFile(excelFilePath);

    // Create output directory
    const outputDir = path.join(__dirname, '..', 'data', 'csv');
    await fs.ensureDir(outputDir);

    console.log('📊 Found sheets:', workbook.SheetNames);

    // Convert each sheet to CSV
    for (const sheetName of workbook.SheetNames) {
      console.log(`\n🔄 Processing sheet: ${sheetName}`);

      const worksheet = workbook.Sheets[sheetName];

      // Convert to CSV
      const csvData = XLSX.utils.sheet_to_csv(worksheet);

      // Save CSV file
      const csvFileName = `${sheetName.replace(/[^a-zA-Z0-9]/g, '_')}.csv`;
      const csvFilePath = path.join(outputDir, csvFileName);

      await fs.writeFile(csvFilePath, csvData, 'utf8');
      console.log(`✅ Saved: ${csvFilePath}`);

      // Also convert to JSON for preview
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      const jsonFileName = `${sheetName.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
      const jsonFilePath = path.join(outputDir, jsonFileName);

      await fs.writeFile(jsonFilePath, JSON.stringify(jsonData, null, 2), 'utf8');
      console.log(`✅ Saved JSON preview: ${jsonFilePath}`);

      // Show first few rows
      console.log(`📋 First 3 rows of ${sheetName}:`);
      console.log(jsonData.slice(0, 3));
    }

    console.log('\n🎉 Excel to CSV conversion completed!');
    console.log(`📁 Output directory: ${outputDir}`);

  } catch (error) {
    console.error('❌ Error converting Excel to CSV:', error.message);
    process.exit(1);
  }
}

// Run the conversion
convertExcelToCSV();