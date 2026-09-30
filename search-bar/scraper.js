const fs = require('fs');
const path = require('path');

const urls = [
  'https://nus-cac.com/',
  'https://nus-cac.com/venue',
  'https://nus-cac.com/funding',
  'https://nus-cac.com/publicity-resources',
  'https://nus-cac.com/student-groups',
  'https://nus-cac.com/equipment-loaning',
  'https://nus-cac.com/about',
  'https://nus-cac.com/production-guide'
];

// Map absolute URLs to their corresponding flat text file names
const backupMapping = {
  'https://nus-cac.com/venue': 'venue.txt',
  'https://nus-cac.com/student-groups': 'student-groups.txt',
  'https://nus-cac.com/about': 'about.txt'
};

function loadLocalBackup(filename) {
  const filePath = path.join(__dirname, 'backups', filename);
  if (fs.existsSync(filePath)) {
    return fs.readFileSync(filePath, 'utf8');
  }
  console.warn(`⚠️ Warning: Backup file '${filename}' not found in backups/ directory.`);
  return "";
}

async function buildIndex() {
  const searchIndex = [];

  for (const url of urls) {
    let title = url; 
    let bodyText = "";

    try {
      console.log(`Fetching site index from: ${url}`);
      
      const response = await fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'
        }
      });

      if (response.ok) {
        const html = await response.text();
        
        const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
        if (titleMatch) title = titleMatch[1].trim();

        const bodyMatch = html.match(/<body[^>]*>([\s\S]+?)<\/body>/i);
        bodyText = bodyMatch ? bodyMatch[1] : html;
      } else {
        console.warn(`⚠️ Hostinger returned status ${response.status}. Relying on local backup.`);
      }
    } catch (error) {
      console.warn(`⚠️ Network fetch failed for ${url}. Relying on local backup.`);
    }

    // 🛡️ GUARANTEED INJECTION LAYER (Powered by local files)
    if (backupMapping[url]) {
      const backupFilename = backupMapping[url];
      const backupContent = loadLocalBackup(backupFilename);
      if (backupContent) {
        console.log(`   └─ Injecting backup dictionary from: backups/${backupFilename}`);
        bodyText += " " + backupContent;
      }
    }

    // Clean up text
    bodyText = bodyText
      .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '') 
      .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')   
      .replace(/<[^>]+>/g, ' ')                         
      .replace(/\s+/g, ' ')                             
      .trim()
      .toLowerCase();

    if (bodyText.length > 0) {
      searchIndex.push({
        title: title,
        url: url,
        content: bodyText
      });
      console.log(`✅ Successfully indexed: "${title}"`);
    } else {
      console.log(`❌ Skipped ${url}: No content and no backup dictionary found.`);
    }
  }

  fs.writeFileSync('search-index.json', JSON.stringify(searchIndex, null, 2));
  console.log(`\n🏁 Successfully wrote ${searchIndex.length} pages to search-index.json!`);
}

buildIndex();