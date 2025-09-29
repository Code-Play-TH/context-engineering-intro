async function globalTeardown(config) {
  console.log('🧹 Global teardown: Cleaning up...');

  // Optional: Clean up test data
  // You might want to keep this minimal for local development

  console.log('✅ Global teardown completed!');
}

module.exports = globalTeardown;