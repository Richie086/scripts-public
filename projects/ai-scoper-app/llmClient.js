const axios = require('axios');

class LLMClient {
  constructor(config = {}) {
    this.provider = config.provider || 'gemini'; // 'gemini' | 'openai' | 'claude' | 'grok' | 'internal'
    this.apiKey = config.apiKey || '';
    this.baseURL = config.baseURL || '';
    this.modelName = config.modelName || '';
    this.customHeaders = config.customHeaders || {};
  }

  async generateContent(prompt, systemInstruction = '', images = []) {
    // If no API Key is provided (except for local/internal), we fall back to a simulation/mock mode
    if (!this.apiKey && this.provider !== 'internal') {
      return this.mockGeneration(prompt, systemInstruction);
    }

    try {
      switch (this.provider) {
        case 'gemini':
          return await this.callGemini(prompt, systemInstruction, images);
        case 'openai':
          return await this.callOpenAI(prompt, systemInstruction, images);
        case 'claude':
          return await this.callClaude(prompt, systemInstruction, images);
        case 'grok':
          return await this.callGrok(prompt, systemInstruction);
        case 'internal':
          return await this.callInternal(prompt, systemInstruction);
        default:
          throw new Error(`Unsupported LLM provider: ${this.provider}`);
      }
    } catch (error) {
      console.error(`LLM Call Error (${this.provider}):`, error.message);
      throw new Error(`LLM Error: ${error.response?.data?.error?.message || error.message}`);
    }
  }

  // --- Gemini API Handler ---
  async callGemini(prompt, systemInstruction, images) {
    const model = this.modelName || 'gemini-1.5-pro';
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${this.apiKey}`;
    
    const contents = [];
    
    // Add images if present
    if (images && images.length > 0) {
      const parts = images.map(img => ({
        inlineData: {
          mimeType: img.mimeType,
          data: img.base64Data
        }
      }));
      parts.push({ text: prompt });
      contents.push({ role: 'user', parts });
    } else {
      contents.push({ role: 'user', parts: [{ text: prompt }] });
    }

    const payload = {
      contents,
      systemInstruction: systemInstruction ? { parts: [{ text: systemInstruction }] } : undefined
    };

    const response = await axios.post(url, payload);
    return response.data.candidates[0].content.parts[0].text;
  }

  // --- OpenAI Handler ---
  async callOpenAI(prompt, systemInstruction, images) {
    const model = this.modelName || 'gpt-4o';
    const url = 'https://api.openai.com/v1/chat/completions';
    
    const messages = [];
    if (systemInstruction) {
      messages.push({ role: 'system', content: systemInstruction });
    }

    if (images && images.length > 0) {
      const contentParts = [{ type: 'text', text: prompt }];
      for (const img of images) {
        contentParts.push({
          type: 'image_url',
          image_url: { url: `data:${img.mimeType};base64,${img.base64Data}` }
        });
      }
      messages.push({ role: 'user', content: contentParts });
    } else {
      messages.push({ role: 'user', content: prompt });
    }

    const response = await axios.post(url, {
      model,
      messages
    }, {
      headers: { Authorization: `Bearer ${this.apiKey}` }
    });

    return response.data.choices[0].message.content;
  }

  // --- Claude Handler ---
  async callClaude(prompt, systemInstruction, images) {
    const model = this.modelName || 'claude-3-5-sonnet-20240620';
    const url = 'https://api.anthropic.com/v1/messages';
    
    const contentParts = [];
    if (images && images.length > 0) {
      for (const img of images) {
        contentParts.push({
          type: 'image',
          source: {
            type: 'base64',
            media_type: img.mimeType,
            data: img.base64Data
          }
        });
      }
    }
    contentParts.push({ type: 'text', text: prompt });

    const response = await axios.post(url, {
      model,
      max_tokens: 4000,
      system: systemInstruction || undefined,
      messages: [{ role: 'user', content: contentParts }]
    }, {
      headers: {
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      }
    });

    return response.data.content[0].text;
  }

  // --- Grok Handler ---
  async callGrok(prompt, systemInstruction) {
    const model = this.modelName || 'grok-beta';
    const url = 'https://api.x.ai/v1/chat/completions';
    
    const messages = [];
    if (systemInstruction) {
      messages.push({ role: 'system', content: systemInstruction });
    }
    messages.push({ role: 'user', content: prompt });

    const response = await axios.post(url, {
      model,
      messages
    }, {
      headers: { Authorization: `Bearer ${this.apiKey}` }
    });

    return response.data.choices[0].message.content;
  }

  // --- Custom Internal/Local Handler (Ollama, local v1) ---
  async callInternal(prompt, systemInstruction) {
    const url = this.baseURL || 'http://localhost:11434/v1/chat/completions';
    const model = this.modelName || 'llama3';
    
    const messages = [];
    if (systemInstruction) {
      messages.push({ role: 'system', content: systemInstruction });
    }
    messages.push({ role: 'user', content: prompt });

    const headers = { ...this.customHeaders };
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await axios.post(url, {
      model,
      messages
    }, { headers });

    return response.data.choices[0].message.content;
  }

  // --- Mock Mode Fallback ---
  mockGeneration(prompt, systemInstruction) {
    console.log('[MOCK LLM] Prompt:', prompt);
    
    if (prompt.includes('interview')) {
      return `### Scoping Clarification Questions
1. **Hosting & Deployment Constraints**: Should this application run inside Docker containers, or directly on local VMs?
2. **Access Control Model**: Do we require multiple user role permissions (e.g. Admin, Editor, Viewer), or simple token auth?
3. **Database Schema Choice**: Do you want a relational SQLite database schema, or a key-value document store?
4. **Data Sync Scheduling**: How often should background synchronization scripts execute?
5. **Security Isolation Limits**: What specific firewall access controls should be applied to prevent external SSH logins?`;
    }

    if (prompt.includes('vulnerabilities') || prompt.includes('security')) {
      return `### Security & Structural Vulnerabilities Report

#### Matched Sensitive Tokens
* No sensitive PII tokens leaked in LLM context.

#### Architectural Scans
1. **Local File Exposure Risk** [Severity: HIGH]
   - *Risk*: Script reads absolute file paths on the local system.
   - *Alternative*: Implement a strict file root path validation utility matching relative routes.
2. **Plaintext Password Variables** [Severity: MEDIUM]
   - *Risk*: hardcoding admin login passwords.
   - *Alternative*: Load passwords from secure environments using SSM parameters or environment variables.

---

### Alternative Solutions
* **Option A: Containerized Microservice**: Package the validation script inside a minimal Alpine Linux Docker container.
* **Option B: Systemd Daemon Handler**: Configure a system daemon with sandbox user restrictions.`;
    }

    if (prompt.includes('tune') || prompt.includes('refine')) {
      return `# Master Scoping Prompt (Refined)
Configure a local Flask web application with SQLite.

## Database Schema (Refined)
* **Users Table**: ID (Integer), Username (Text, unique), PasswordHash (Text), CreatedAt (Timestamp).
* **Photos Table**: ID (Integer), Path (Text), TakenAt (Timestamp), OwnerID (Integer).

## Security Checklist
* Use bcrypt for password hashing.
* Restrict SSH port access.`;
    }

    // Default concept expansion output
    return `# Concept Expansion: Private Local Flask Photo Tracker

A secure local Flask web application designed for private image tracking, indexing, and automated EXIF tag parsing.

## 1. Feature Decomposition
* **Automated EXIF Metadata Parsing**: Extracted creation dates are mapped automatically to database fields.
* **Responsive Image Layout Board**: Flexbox CSS card columns styling.
* **Local Storage Directory Sync**: Background scans matching absolute local image paths.

## 2. Core Technical Challenges
* Sandboxed file reading permissions for image file parsing.
* Performance overhead when indexing directory pathways containing thousands of image files.`;
  }
}

module.exports = LLMClient;
