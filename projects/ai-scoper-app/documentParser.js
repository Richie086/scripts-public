const fs = require('fs');
const path = require('path');
const mammoth = require('mammoth');
const pdfParse = require('pdf-parse');

class DocumentParser {
  /**
   * Main router to parse file based on extension.
   */
  static async parseFile(filePath) {
    if (!fs.existsSync(filePath)) {
      throw new Error(`File does not exist: ${filePath}`);
    }

    const ext = path.extname(filePath).toLowerCase();
    
    switch (ext) {
      case '.txt':
      case '.md':
      case '.csv':
      case '.xml':
      case '.json':
      case '.html':
        return fs.readFileSync(filePath, 'utf8');
        
      case '.docx':
        return await this.parseDocx(filePath);
        
      case '.pdf':
        return await this.parsePdf(filePath);
        
      case '.png':
      case '.jpg':
      case '.jpeg':
      case '.webp':
      case '.gif':
        return await this.parseImage(filePath);
        
      default:
        // Try reading as text by default
        try {
          return fs.readFileSync(filePath, 'utf8');
        } catch {
          throw new Error(`Unsupported binary format: ${ext}`);
        }
    }
  }

  // --- Word DocX Parser ---
  static async parseDocx(filePath) {
    const result = await mammoth.extractRawText({ path: filePath });
    return result.value; // Clean plaintext
  }

  // --- PDF Parser ---
  static async parsePdf(filePath) {
    const dataBuffer = fs.readFileSync(filePath);
    const data = await pdfParse(dataBuffer);
    return data.text; // Extracted text
  }

  // --- Image Converter for Multimodal inputs ---
  static async parseImage(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    let mimeType = 'image/png';
    if (ext === '.jpg' || ext === '.jpeg') mimeType = 'image/jpeg';
    else if (ext === '.webp') mimeType = 'image/webp';
    else if (ext === '.gif') mimeType = 'image/gif';

    const base64Data = fs.readFileSync(filePath).toString('base64');
    return {
      isImage: true,
      mimeType,
      base64Data,
      fileName: path.basename(filePath)
    };
  }
}

module.exports = DocumentParser;
