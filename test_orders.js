const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Navigate to Orders page
  await page.goto('http://localhost:3000/orders', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  
  // Check if section tabs exist
  const allOrdersTab = await page.$('.tab-button:has-text("All Orders")');
  const submittedOrdersTab = await page.$('.tab-button:has-text("Submitted")');
  
  console.log('✓ Orders page loaded');
  console.log('All Orders tab:', allOrdersTab ? '✓ Found' : '✗ Not found');
  console.log('Submitted Orders tab:', submittedOrdersTab ? '✓ Found' : '✗ Not found');
  
  // Check table structure
  const table = await page.$('.orders-table');
  console.log('Orders table:', table ? '✓ Found' : '✗ Not found');
  
  // Get table headers
  const headers = await page.$$('.orders-table th');
  console.log(`Table headers count: ${headers.length}`);
  
  // Check for lead time header
  const leadTimeHeader = await page.textContent('.col-leadtime');
  console.log('Lead time column:', leadTimeHeader ? '✓ Found' : '✗ Not visible (expected - All Orders tab active)');
  
  // Click on Submitted Orders tab
  const submitBtn = await page.$('button:has-text("Submitted")');
  if (submitBtn) {
    await submitBtn.click();
    await page.waitForTimeout(500);
    
    // Check for lead time column after switching tabs
    const leadTimeCol = await page.$('.col-leadtime');
    console.log('Lead time column (after switching):', leadTimeCol ? '✓ Visible on Submitted tab' : '✗ Not found');
  }
  
  // Get page HTML to inspect structure
  const html = await page.content();
  const hasSectionTabs = html.includes('section-tabs');
  const hasTabButton = html.includes('tab-button');
  
  console.log('\nStructure check:');
  console.log('section-tabs class:', hasSectionTabs ? '✓ Present' : '✗ Missing');
  console.log('tab-button class:', hasTabButton ? '✓ Present' : '✗ Missing');
  
  await browser.close();
})();
