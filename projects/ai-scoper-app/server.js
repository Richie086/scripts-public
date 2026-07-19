const express = require('express');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');
const LLMClient = require('./llmClient');
const SecurityScanner = require('./securityScanner');
const DocumentParser = require('./documentParser');

const app = express();
const PORT = process.env.PORT || 5070;

app.use(express.json({ limit: '50mb' }));
app.use(express.static(path.join(__dirname, 'public')));

const scanner = new SecurityScanner();

// 1. Secrets Scanner Endpoint
app.post('/api/scan', (req, res) => {
  const { text } = req.body;
  const results = scanner.scan(text);
  res.json(results);
});

// Helper to construct LLM client from request headers/body
function getLLMClient(req) {
  const { provider, apiKey, baseURL, modelName, customHeaders } = req.body.config || {};
  
  let headersObj = {};
  if (customHeaders) {
    if (typeof customHeaders === 'object') {
      headersObj = customHeaders;
    } else if (typeof customHeaders === 'string') {
      try {
        headersObj = JSON.parse(customHeaders);
      } catch (e) {
        console.error('Failed to parse customHeaders string:', e);
      }
    }
  }

  return new LLMClient({ provider, apiKey, baseURL, modelName, customHeaders: headersObj });
}

// 2. Expand Concept Endpoint
app.post('/api/expand', async (req, res) => {
  try {
    const { concept, images } = req.body;
    const client = getLLMClient(req);

    const systemInstruction = "You are a senior Jira project manager and software architect. Expand the user's software concept into a highly structured list of Jira Epics, Tasks, and Subtasks. You MUST structure the output using the following markdown format: use '# Epic: [Title]' for Epics, '## Task: [Title]' for Tasks/Stories, and '### Subtask: [Title]' for Subtasks. For each item, provide a clear description and suggested labels (e.g. 'Labels: auth, infra') on a new line.";
    const result = await client.generateContent(concept, systemInstruction, images);
    res.json({ expandedConcept: result });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 3. Clarification Questions Endpoint
app.post('/api/interview/questions', async (req, res) => {
  try {
    const { expandedConcept } = req.body;
    const client = getLLMClient(req);

    const systemInstruction = "You are a senior scoping interviewer. Generate exactly 5 highly specific functional or technical questions to ask the user to clarify gaps or features in their specifications.";
    const result = await client.generateContent(
      `Please review the expanded spec: \n\n${expandedConcept}\n\nWhat are 5 core questions to clarify the implementation?`,
      systemInstruction
    );
    res.json({ questions: result });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 4. Security & Alternatives Endpoint
app.post('/api/analyze/vulnerabilities', async (req, res) => {
  try {
    const { concept } = req.body;
    const client = getLLMClient(req);

    const systemInstruction = "You are a security auditor and systems engineer. Analyze the software concept for architectural, database, hosting, or input vulnerabilities, then suggest 2 design alternatives.";
    const result = await client.generateContent(concept, systemInstruction);
    res.json({ vulnerabilities: result });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 5. Generate Master Prompt Endpoint
app.post('/api/prompt/generate', async (req, res) => {
  try {
    const { concept, interviewAnswers, vulnerabilities } = req.body;
    const client = getLLMClient(req);

    const systemInstruction = "You are a master prompt engineer. Generate a comprehensive system instructions prompt that can be fed to a coding agent to build this application.";
    const promptPayload = `
Concept: ${concept}
Interview Clarifications: ${interviewAnswers}
Security Considerations: ${vulnerabilities}

Please compile this into a unified master system coding prompt.
`;
    const result = await client.generateContent(promptPayload, systemInstruction);
    res.json({ masterPrompt: result });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 6. Conversational Prompt Tuning Endpoint
app.post('/api/prompt/tune', async (req, res) => {
  try {
    const { currentPrompt, tuningInstruction } = req.body;
    const client = getLLMClient(req);

    const systemInstruction = "You are a prompt optimizer. Modify the current system prompt based on the user's feedback, tuning instructions, or new features. Return the updated prompt as clean markdown.";
    const payload = `
Current Prompt:
${currentPrompt}

Tuning Feedback:
${tuningInstruction}
`;
    const result = await client.generateContent(payload, systemInstruction);
    res.json({ tunedPrompt: result });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// 7. Syntax Engine Validation Endpoint
app.post('/api/syntax/check', (req, res) => {
  const { code, language } = req.body;
  if (!code) return res.status(400).json({ error: 'No code content provided' });

  // Generate temporary file name
  const tempId = Math.random().toString(36).substring(7);
  let ext = '.txt';
  if (language === 'python') ext = '.py';
  else if (language === 'javascript') ext = '.js';

  const tempFilePath = path.join(__dirname, `temp_check_${tempId}${ext}`);
  fs.writeFileSync(tempFilePath, code);

  let command = '';
  if (language === 'python') {
    command = `python3 -m py_compile ${tempFilePath}`;
  } else if (language === 'javascript') {
    command = `node -c ${tempFilePath}`;
  } else {
    // Unsupported compiler, use a simulated regex or placeholder pass
    fs.unlinkSync(tempFilePath);
    return res.json({ success: true, message: `Syntax validation mock-passed for ${language}.` });
  }

  exec(command, (err, stdout, stderr) => {
    // Delete temp file immediately
    if (fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }

    if (err) {
      // Return syntax error output
      return res.json({
        success: false,
        error: stderr || stdout || err.message
      });
    }

    res.json({
      success: true,
      message: 'Syntax Check Passed successfully.'
    });
  });
});

// 8. Multi-Format Exporter Endpoint
app.post('/api/export', (req, res) => {
  const { content, format, docName } = req.body;
  const fileName = `${docName || 'ai-scoping-document'}.${format}`;

  res.setHeader('Content-Disposition', `attachment; filename=${fileName}`);
  
  if (format === 'json') {
    res.setHeader('Content-Type', 'application/json');
    return res.send(JSON.stringify({ content }, null, 2));
  }
  if (format === 'csv') {
    res.setHeader('Content-Type', 'text/csv');
    
    const lines = content.split('\n');
    const rows = [['Issue ID', 'Summary', 'Description', 'Issue Type', 'Parent ID', 'Labels']];
    let currentEpicId = '';
    let currentTaskId = '';
    let currentIssueId = 0;
    
    let currentDescription = [];
    let currentSummary = '';
    let currentType = '';
    let currentLabels = '';
    
    const flushPreviousIssue = () => {
      if (currentSummary) {
        let parentId = '';
        if (currentType === 'Task' || currentType === 'Story') {
          parentId = currentEpicId;
        } else if (currentType === 'Sub-task') {
          parentId = currentTaskId;
        }
        
        rows.push([
          currentIssueId.toString(),
          currentSummary,
          currentDescription.join(' ').trim(),
          currentType,
          parentId,
          currentLabels
        ]);
        
        if (currentType === 'Epic') {
          currentEpicId = currentIssueId.toString();
        } else if (currentType === 'Task' || currentType === 'Story') {
          currentTaskId = currentIssueId.toString();
        }
        
        currentSummary = '';
        currentDescription = [];
        currentType = '';
        currentLabels = '';
      }
    };
    
    for (let line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      
      if (trimmed.startsWith('# ')) {
        flushPreviousIssue();
        currentIssueId++;
        currentSummary = trimmed.substring(2).replace(/Epic:\s*/i, '').trim();
        currentType = 'Epic';
      } else if (trimmed.startsWith('## ')) {
        flushPreviousIssue();
        currentIssueId++;
        currentSummary = trimmed.substring(3).replace(/(Task|Story):\s*/i, '').trim();
        currentType = 'Task';
      } else if (trimmed.startsWith('### ')) {
        flushPreviousIssue();
        currentIssueId++;
        currentSummary = trimmed.substring(4).replace(/Subtask:\s*/i, '').trim();
        currentType = 'Sub-task';
      } else if (trimmed.toLowerCase().startsWith('labels:')) {
        currentLabels = trimmed.substring(7).trim();
      } else {
        currentDescription.push(trimmed);
      }
    }
    flushPreviousIssue(); // flush the final active issue
    
    const csvContent = rows.map(row => 
      row.map(cell => `"${cell.replace(/"/g, '""')}"`).join(',')
    ).join('\n');
    
    return res.send(csvContent);
  }
  if (format === 'xml') {
    res.setHeader('Content-Type', 'application/xml');
    const xmlContent = `<?xml version="1.0" encoding="UTF-8"?>\n<document>\n  <title>${docName}</title>\n  <body><![CDATA[${content}]]></body>\n</document>`;
    return res.send(xmlContent);
  }
  if (format === 'html') {
    res.setHeader('Content-Type', 'text/html');
    const htmlContent = `<html><head><title>${docName}</title><style>body { font-family: sans-serif; padding: 40px; background: #282a36; color: #f8f8f2; }</style></head><body>${content.replace(/\n/g, '<br>')}</body></html>`;
    return res.send(htmlContent);
  }

  // Fallback as plain text/markdown
  res.setHeader('Content-Type', 'text/plain');
  res.send(content);
});

// 9. Git-Branch Verification Endpoint
app.post('/api/git/branch', (req, res) => {
  // Checks out 'dev' branch from 'main'
  const gitRoot = path.resolve(__dirname, '../../');
  
  exec('git checkout -b dev', { cwd: gitRoot }, (err, stdout, stderr) => {
    // If branch already exists, just switch to it
    if (err && stderr.includes('already exists')) {
      exec('git checkout dev', { cwd: gitRoot }, (err2, stdout2, stderr2) => {
        if (err2) {
          return res.json({ success: false, error: stderr2 || err2.message });
        }
        return res.json({ success: true, message: 'Checked out existing dev branch.' });
      });
    } else if (err) {
      return res.json({ success: false, error: stderr || err.message });
    } else {
      res.json({ success: true, message: 'Created and checked out dev branch from main.' });
    }
  });
});

// 10. Serve rendered Implementation Plan
app.get('/api/plan', (req, res) => {
  const fs = require('fs');
  const planPath = '/home/rtroiano/.gemini/antigravity-cli/brain/5bac2cd3-828d-42f1-a375-cc94a3a19bcf/ai_scoper_app_plan.md';
  if (!fs.existsSync(planPath)) {
    return res.status(404).send('Plan file not found.');
  }
  const content = fs.readFileSync(planPath, 'utf8');
  
  // Convert markdown format to HTML
  let html = content
    .replace(/^#\s+(.*)$/gm, '<h1>$1</h1>')
    .replace(/^##\s+(.*)$/gm, '<h2>$1</h2>')
    .replace(/^###\s+(.*)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^-\s+(.*)$/gm, '<li>$1</li>')
    .replace(/^\*\s+(.*)$/gm, '<li>$1</li>')
    .replace(/([^>\r\n]?)(\r\n|\n\r|\r|\n)/g, '$1<br>$2');

  const page = `<html><head><title>AI Jira Scoper Plan</title><style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 40px; background: #282a36; color: #f8f8f2; line-height: 1.6; max-width: 800px; margin: 0 auto; }
    h1, h2, h3 { color: #bd93f9; margin-top: 30px; }
    li { margin-left: 20px; }
  </style></head><body>${html}</body></html>`;
  res.send(page);
});

// 11. Serve rendered generic documentation file
app.get('/api/docs/:filename', (req, res) => {
  const fs = require('fs');
  const path = require('path');
  const filename = req.params.filename;
  const safeFilename = path.basename(filename);
  
  let docName = safeFilename;
  if (!docName.endsWith('.md')) {
    docName += '.md';
  }
  
  const docPath = path.join('/home/rtroiano/.gemini/antigravity-cli/brain/5bac2cd3-828d-42f1-a375-cc94a3a19bcf', docName);
  if (!fs.existsSync(docPath)) {
    return res.status(404).send('Document file not found.');
  }
  
  const content = fs.readFileSync(docPath, 'utf8');
  let html = content
    .replace(/^#\s+(.*)$/gm, '<h1>$1</h1>')
    .replace(/^##\s+(.*)$/gm, '<h2>$1</h2>')
    .replace(/^###\s+(.*)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/^-\s+(.*)$/gm, '<li>$1</li>')
    .replace(/^\*\s+(.*)$/gm, '<li>$1</li>')
    .replace(/([^>\r\n]?)(\r\n|\n\r|\r|\n)/g, '$1<br>$2');

  const page = `<html><head><title>AI Jira Scoper Docs - ${safeFilename}</title><style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 40px; background: #282a36; color: #f8f8f2; line-height: 1.6; max-width: 800px; margin: 0 auto; }
    h1, h2, h3 { color: #bd93f9; margin-top: 30px; }
    li { margin-left: 20px; }
  </style></head><body>${html}</body></html>`;
  res.send(page);
});

app.listen(PORT, () => {
  console.log(`AI Scoper backend running on http://localhost:${PORT}`);
});

module.exports = app;
