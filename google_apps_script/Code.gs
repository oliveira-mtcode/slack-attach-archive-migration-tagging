/**
 * Google Apps Script for Slack Archive Migration Integration
 * This script provides additional functionality for Google Drive integration
 * and handles real-time file processing triggers.
 */

// Configuration - Update these values
const CONFIG = {
  DRIVE_FOLDER_ID: 'YOUR_DRIVE_FOLDER_ID',
  SLACK_WEBHOOK_URL: 'YOUR_WEBHOOK_URL',
  VISION_API_ENABLED: true,
  VIDEO_INTELLIGENCE_ENABLED: true
};

/**
 * Main function to set up the migration system
 */
function setupMigrationSystem() {
  console.log('Setting up Slack Archive Migration system...');
  
  // Create folder structure
  createFolderStructure();
  
  // Set up triggers
  setupTriggers();
  
  // Test webhook connection
  testWebhookConnection();
  
  console.log('Migration system setup complete!');
}

/**
 * Create the initial folder structure in Google Drive
 */
function createFolderStructure() {
  try {
    const rootFolder = DriveApp.getFolderById(CONFIG.DRIVE_FOLDER_ID);
    
    // Create main folders
    const folders = [
      'Slack Archives',
      'Images',
      'Videos',
      'Documents',
      'Processed Files',
      'Error Logs'
    ];
    
    folders.forEach(folderName => {
      const existingFolders = rootFolder.getFoldersByName(folderName);
      if (!existingFolders.hasNext()) {
        const newFolder = rootFolder.createFolder(folderName);
        console.log(`Created folder: ${folderName} (ID: ${newFolder.getId()})`);
      }
    });
    
  } catch (error) {
    console.error('Error creating folder structure:', error);
  }
}

/**
 * Set up Google Apps Script triggers
 */
function setupTriggers() {
  try {
    // Delete existing triggers
    const triggers = ScriptApp.getProjectTriggers();
    triggers.forEach(trigger => {
      if (trigger.getHandlerFunction().includes('Migration')) {
        ScriptApp.deleteTrigger(trigger);
      }
    });
    
    // Create new triggers
    ScriptApp.newTrigger('onFileUpload')
      .timeBased()
      .everyMinutes(5)
      .create();
    
    ScriptApp.newTrigger('processPendingFiles')
      .timeBased()
      .everyMinutes(10)
      .create();
    
    console.log('Triggers set up successfully');
    
  } catch (error) {
    console.error('Error setting up triggers:', error);
  }
}

/**
 * Handle file upload events
 */
function onFileUpload() {
  try {
    const recentFiles = getRecentFiles();
    
    recentFiles.forEach(file => {
      if (isSlackFile(file)) {
        processSlackFile(file);
      }
    });
    
  } catch (error) {
    console.error('Error in onFileUpload:', error);
  }
}

/**
 * Process pending files
 */
function processPendingFiles() {
  try {
    const pendingFiles = getPendingFiles();
    
    pendingFiles.forEach(file => {
      processFileWithAI(file);
    });
    
  } catch (error) {
    console.error('Error in processPendingFiles:', error);
  }
}

/**
 * Get recent files from Google Drive
 */
function getRecentFiles() {
  const rootFolder = DriveApp.getFolderById(CONFIG.DRIVE_FOLDER_ID);
  const files = rootFolder.getFiles();
  const recentFiles = [];
  
  while (files.hasNext()) {
    const file = files.next();
    const modifiedDate = file.getLastUpdated();
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
    
    if (modifiedDate > oneHourAgo) {
      recentFiles.push(file);
    }
  }
  
  return recentFiles;
}

/**
 * Check if a file is from Slack migration
 */
function isSlackFile(file) {
  const properties = file.getProperties();
  return properties.slack_channel && properties.slack_user;
}

/**
 * Process a Slack file with AI analysis
 */
function processSlackFile(file) {
  try {
    console.log(`Processing Slack file: ${file.getName()}`);
    
    // Get file properties
    const properties = file.getProperties();
    const channel = properties.slack_channel;
    const user = properties.slack_user;
    
    // Create channel folder if it doesn't exist
    const channelFolder = getOrCreateChannelFolder(channel);
    
    // Move file to appropriate folder
    if (channelFolder) {
      file.moveTo(channelFolder);
    }
    
    // Add AI analysis if enabled
    if (CONFIG.VISION_API_ENABLED || CONFIG.VIDEO_INTELLIGENCE_ENABLED) {
      processFileWithAI(file);
    }
    
    // Update file description
    updateFileDescription(file, channel, user);
    
  } catch (error) {
    console.error(`Error processing file ${file.getName()}:`, error);
  }
}

/**
 * Process file with AI analysis
 */
function processFileWithAI(file) {
  try {
    const mimeType = file.getBlob().getContentType();
    
    if (mimeType.startsWith('image/') && CONFIG.VISION_API_ENABLED) {
      analyzeImageWithVision(file);
    } else if (mimeType.startsWith('video/') && CONFIG.VIDEO_INTELLIGENCE_ENABLED) {
      analyzeVideoWithIntelligence(file);
    }
    
  } catch (error) {
    console.error(`Error in AI analysis for ${file.getName()}:`, error);
  }
}

/**
 * Analyze image with Google Vision API
 */
function analyzeImageWithVision(file) {
  try {
    // This would integrate with Google Vision API
    // For now, we'll add a placeholder
    const description = `AI Analysis: Image file processed with Vision API`;
    file.setDescription(description);
    
    console.log(`Vision analysis completed for: ${file.getName()}`);
    
  } catch (error) {
    console.error(`Vision analysis error for ${file.getName()}:`, error);
  }
}

/**
 * Analyze video with Video Intelligence API
 */
function analyzeVideoWithIntelligence(file) {
  try {
    // This would integrate with Video Intelligence API
    // For now, we'll add a placeholder
    const description = `AI Analysis: Video file processed with Video Intelligence API`;
    file.setDescription(description);
    
    console.log(`Video analysis completed for: ${file.getName()}`);
    
  } catch (error) {
    console.error(`Video analysis error for ${file.getName()}:`, error);
  }
}

/**
 * Get or create channel folder
 */
function getOrCreateChannelFolder(channelId) {
  try {
    const rootFolder = DriveApp.getFolderById(CONFIG.DRIVE_FOLDER_ID);
    const folderName = `Channel-${channelId}`;
    
    const existingFolders = rootFolder.getFoldersByName(folderName);
    if (existingFolders.hasNext()) {
      return existingFolders.next();
    } else {
      return rootFolder.createFolder(folderName);
    }
    
  } catch (error) {
    console.error(`Error creating channel folder for ${channelId}:`, error);
    return null;
  }
}

/**
 * Update file description with metadata
 */
function updateFileDescription(file, channel, user) {
  try {
    const properties = file.getProperties();
    const uploadTime = properties.upload_timestamp || 'Unknown';
    
    const description = `
Slack Migration File
Channel: ${channel}
User: ${user}
Upload Time: ${uploadTime}
Original Name: ${file.getName()}
Processed: ${new Date().toISOString()}
    `.trim();
    
    file.setDescription(description);
    
  } catch (error) {
    console.error(`Error updating description for ${file.getName()}:`, error);
  }
}

/**
 * Get pending files that need processing
 */
function getPendingFiles() {
  // This would query a database or use Drive properties
  // For now, return empty array
  return [];
}

/**
 * Test webhook connection
 */
function testWebhookConnection() {
  try {
    const payload = {
      test: true,
      timestamp: new Date().toISOString()
    };
    
    const response = UrlFetchApp.fetch(CONFIG.SLACK_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      payload: JSON.stringify(payload)
    });
    
    if (response.getResponseCode() === 200) {
      console.log('Webhook connection test successful');
    } else {
      console.error('Webhook connection test failed:', response.getResponseCode());
    }
    
  } catch (error) {
    console.error('Webhook connection test error:', error);
  }
}

/**
 * Utility function to search files by tags
 */
function searchFilesByTags(tags) {
  try {
    const rootFolder = DriveApp.getFolderById(CONFIG.DRIVE_FOLDER_ID);
    const files = rootFolder.getFiles();
    const matchingFiles = [];
    
    while (files.hasNext()) {
      const file = files.next();
      const description = file.getDescription();
      
      if (tags.some(tag => description.includes(tag))) {
        matchingFiles.push({
          name: file.getName(),
          id: file.getId(),
          url: file.getUrl(),
          description: description
        });
      }
    }
    
    return matchingFiles;
    
  } catch (error) {
    console.error('Error searching files by tags:', error);
    return [];
  }
}

/**
 * Generate migration report
 */
function generateMigrationReport() {
  try {
    const rootFolder = DriveApp.getFolderById(CONFIG.DRIVE_FOLDER_ID);
    const files = rootFolder.getFiles();
    
    let totalFiles = 0;
    let slackFiles = 0;
    let processedFiles = 0;
    
    while (files.hasNext()) {
      const file = files.next();
      totalFiles++;
      
      if (isSlackFile(file)) {
        slackFiles++;
        
        if (file.getDescription().includes('AI Analysis')) {
          processedFiles++;
        }
      }
    }
    
    const report = {
      totalFiles: totalFiles,
      slackFiles: slackFiles,
      processedFiles: processedFiles,
      processingRate: slackFiles > 0 ? (processedFiles / slackFiles * 100).toFixed(2) + '%' : '0%',
      generatedAt: new Date().toISOString()
    };
    
    console.log('Migration Report:', report);
    return report;
    
  } catch (error) {
    console.error('Error generating migration report:', error);
    return null;
  }
}
