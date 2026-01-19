/**
 * GMAIL APPS SCRIPT FOR NEWSLETTER INBOX
 * 
 * This script automatically syncs newsletters from a Gmail label to your app.
 * 
 * SETUP INSTRUCTIONS:
 * 
 * 1. Go to https://script.google.com
 * 2. Create a new project
 * 3. Paste this entire script
 * 4. Update YOUR_WEBHOOK_URL below (or leave empty to use local file)
 * 5. Run the setup() function once
 * 6. Authorize the script when prompted
 * 7. Set up a time trigger to run processNewEmails() every hour
 * 
 * HOW TO USE:
 * - Create a Gmail filter for newsletters you want to track
 * - Have the filter apply a label called "AI-Inbox"
 * - The script will automatically process new emails with this label
 */

// ============================================================================
// CONFIGURATION - Edit these values
// ============================================================================

const CONFIG = {
  // The Gmail label to watch for newsletters
  LABEL_NAME: "AI-Inbox",
  
  // Your webhook URL (from email_receiver.py running on your server)
  // Leave empty if you want to save to Google Drive instead
  WEBHOOK_URL: "",
  
  // API key for webhook (must match INBOX_API_KEY in your .env)
  API_KEY: "developai-inbox-2024",
  
  // Google Drive folder name (if not using webhook)
  DRIVE_FOLDER: "Newsletter-Inbox-Export",
  
  // Label to apply after processing
  PROCESSED_LABEL: "AI-Inbox-Processed"
};

// ============================================================================
// MAIN FUNCTIONS
// ============================================================================

/**
 * Run this once to set up labels
 */
function setup() {
  // Create the processed label if it doesn't exist
  let label = GmailApp.getUserLabelByName(CONFIG.PROCESSED_LABEL);
  if (!label) {
    GmailApp.createLabel(CONFIG.PROCESSED_LABEL);
    Logger.log("Created label: " + CONFIG.PROCESSED_LABEL);
  }
  
  // Create the inbox label if it doesn't exist
  label = GmailApp.getUserLabelByName(CONFIG.LABEL_NAME);
  if (!label) {
    GmailApp.createLabel(CONFIG.LABEL_NAME);
    Logger.log("Created label: " + CONFIG.LABEL_NAME);
  }
  
  Logger.log("Setup complete! Now:");
  Logger.log("1. Create a Gmail filter for newsletters");
  Logger.log("2. Have it apply the label: " + CONFIG.LABEL_NAME);
  Logger.log("3. Set up a time trigger for processNewEmails()");
}

/**
 * Process new emails - run this on a schedule (hourly recommended)
 */
function processNewEmails() {
  const label = GmailApp.getUserLabelByName(CONFIG.LABEL_NAME);
  const processedLabel = GmailApp.getUserLabelByName(CONFIG.PROCESSED_LABEL);
  
  if (!label) {
    Logger.log("Label not found: " + CONFIG.LABEL_NAME);
    return;
  }
  
  // Get threads with the inbox label but not the processed label
  const threads = label.getThreads(0, 50);
  let processedCount = 0;
  
  for (const thread of threads) {
    // Skip if already processed
    const labels = thread.getLabels().map(l => l.getName());
    if (labels.includes(CONFIG.PROCESSED_LABEL)) {
      continue;
    }
    
    // Get the first message in the thread
    const messages = thread.getMessages();
    for (const message of messages) {
      const emailData = extractEmailData(message);
      
      // Send to webhook or save to Drive
      if (CONFIG.WEBHOOK_URL) {
        sendToWebhook(emailData);
      } else {
        saveToDrive(emailData);
      }
      
      processedCount++;
    }
    
    // Mark as processed
    if (processedLabel) {
      thread.addLabel(processedLabel);
    }
  }
  
  Logger.log("Processed " + processedCount + " emails");
}

/**
 * Extract data from a Gmail message
 */
function extractEmailData(message) {
  return {
    from: message.getFrom(),
    subject: message.getSubject(),
    date: message.getDate().toISOString(),
    body: message.getPlainBody(),
    html: message.getBody(),
  };
}

/**
 * Send email data to webhook
 */
function sendToWebhook(emailData) {
  try {
    const response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL, {
      method: 'post',
      contentType: 'application/json',
      headers: {
        'X-API-Key': CONFIG.API_KEY
      },
      payload: JSON.stringify(emailData),
      muteHttpExceptions: true
    });
    
    Logger.log("Webhook response: " + response.getContentText());
  } catch (error) {
    Logger.log("Webhook error: " + error.toString());
  }
}

/**
 * Save email data to Google Drive (alternative to webhook)
 */
function saveToDrive(emailData) {
  // Get or create the folder
  let folder;
  const folders = DriveApp.getFoldersByName(CONFIG.DRIVE_FOLDER);
  
  if (folders.hasNext()) {
    folder = folders.next();
  } else {
    folder = DriveApp.createFolder(CONFIG.DRIVE_FOLDER);
  }
  
  // Create a file for this email
  const filename = Utilities.formatDate(new Date(), "GMT", "yyyy-MM-dd_HH-mm-ss") + 
                   "_" + emailData.subject.substring(0, 30).replace(/[^a-zA-Z0-9]/g, "_") + 
                   ".json";
  
  folder.createFile(filename, JSON.stringify(emailData, null, 2), MimeType.PLAIN_TEXT);
  
  Logger.log("Saved to Drive: " + filename);
}

/**
 * Manual test - process a single recent email
 */
function testWithRecentEmail() {
  const threads = GmailApp.getInboxThreads(0, 1);
  if (threads.length > 0) {
    const message = threads[0].getMessages()[0];
    const emailData = extractEmailData(message);
    
    Logger.log("Subject: " + emailData.subject);
    Logger.log("From: " + emailData.from);
    Logger.log("Body preview: " + emailData.body.substring(0, 200));
    
    // Try saving to Drive as a test
    saveToDrive(emailData);
  }
}

// ============================================================================
// TRIGGER SETUP
// ============================================================================

/**
 * Set up automatic hourly processing
 */
function createHourlyTrigger() {
  // Delete existing triggers for this function
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === 'processNewEmails') {
      ScriptApp.deleteTrigger(trigger);
    }
  }
  
  // Create new hourly trigger
  ScriptApp.newTrigger('processNewEmails')
    .timeBased()
    .everyHours(1)
    .create();
  
  Logger.log("Created hourly trigger for processNewEmails()");
}

/**
 * Remove the automatic trigger
 */
function removeHourlyTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  for (const trigger of triggers) {
    if (trigger.getHandlerFunction() === 'processNewEmails') {
      ScriptApp.deleteTrigger(trigger);
      Logger.log("Removed trigger");
    }
  }
}









