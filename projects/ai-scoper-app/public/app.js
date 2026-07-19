/* ==============================================================================
   Logic: app.js
   Frontend controllers for managing tab navigation, file drop, secrets scrubbing,
   live formatting, AI prompt tuner, syntax checker, and exports.
   ============================================================================== */

document.addEventListener('DOMContentLoaded', () => {

  // --- State Variables ---
  let activeTab = 'tab-expand';
  let uploadedFiles = []; // [{ name, content, isImage, mimeType, base64Data }]
  let expandedConcept = '';
  let interviewQuestions = '';
  let securityVulnerabilities = '';
  let masterPrompt = '';

  // --- Element Selectors ---
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');
  
  const providerSelect = document.getElementById('provider-select');
  const apiKeyInput = document.getElementById('api-key-input');
  const modelNameInput = document.getElementById('model-name-input');
  const baseUrlInput = document.getElementById('base-url-input');
  const baseUrlGroup = document.getElementById('base-url-group');
  const customHeadersGroup = document.getElementById('custom-headers-group');
  const customHeadersInput = document.getElementById('custom-headers-input');
  const customHeadersValidation = document.getElementById('custom-headers-validation');
  const themeSelect = document.getElementById('theme-select');
  
  const gitDevBtn = document.getElementById('git-dev-btn');
  const gitStatusLog = document.getElementById('git-status-log');
  
  const fileDropzone = document.getElementById('file-dropzone');
  const fileInput = document.getElementById('file-input');
  const uploadedFilesList = document.getElementById('uploaded-files-list');
  const conceptTextarea = document.getElementById('concept-textarea');
  const redactBanner = document.getElementById('redaction-banner');
  const redactAllBtn = document.getElementById('redact-all-btn');
  
  const expandBtn = document.getElementById('expand-btn');
  const expandOutputCard = document.getElementById('expand-output-card');
  const expandOutputRendered = document.getElementById('expand-output-rendered');
  const acceptExpandBtn = document.getElementById('accept-expand-btn');
  const regenerateExpandBtn = document.getElementById('regenerate-expand-btn');
  const discardExpandBtn = document.getElementById('discard-expand-btn');
  
  const fixHeadingsBtn = document.getElementById('fix-headings-btn');
  const fixTablesBtn = document.getElementById('fix-tables-btn');
  
  const questionsContainer = document.getElementById('questions-container');
  const submitInterviewBtn = document.getElementById('submit-interview-btn');
  
  const securityContent = document.getElementById('security-content');
  
  const syntaxLangSelect = document.getElementById('syntax-lang-select');
  const syntaxCodeArea = document.getElementById('syntax-code-area');
  const syntaxResultAlert = document.getElementById('syntax-result-alert');
  const checkSyntaxBtn = document.getElementById('check-syntax-btn');
  
  const promptWorkspace = document.getElementById('prompt-workspace');
  const chatInput = document.getElementById('chat-input');
  const chatSendBtn = document.getElementById('chat-send-btn');
  const chatMessagesContainer = document.getElementById('chat-messages-container');
  
  const exportFormatSelect = document.getElementById('export-format-select');
  const exportBtn = document.getElementById('export-btn');

  // --- 1. Tab Navigation Routing ---
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));
      
      btn.classList.add('active');
      document.getElementById(target).classList.add('active');
      activeTab = target;
    });
  });

  // --- Color Scheme Theme Switcher ---
  themeSelect.addEventListener('change', () => {
    const theme = themeSelect.value;
    document.body.className = theme;
    localStorage.setItem('SELECTED_THEME', theme);
  });
  // Load persisted theme
  const savedTheme = localStorage.getItem('SELECTED_THEME') || 'theme-dracula';
  document.body.className = savedTheme;
  themeSelect.value = savedTheme;

  // --- 2. LLM Provider Selector Config drawer ---
  providerSelect.addEventListener('change', () => {
    const val = providerSelect.value;
    if (val === 'internal') {
      baseUrlGroup.classList.remove('hidden');
      customHeadersGroup.classList.remove('hidden');
    } else {
      baseUrlGroup.classList.add('hidden');
      customHeadersGroup.classList.add('hidden');
    }
  });

  // Live JSON validation for custom headers input
  customHeadersInput.addEventListener('input', () => {
    const val = customHeadersInput.value.trim();
    if (!val) {
      customHeadersValidation.style.display = 'none';
      customHeadersInput.style.borderColor = '';
      return;
    }
    try {
      JSON.parse(val);
      customHeadersValidation.style.display = 'none';
      customHeadersInput.style.borderColor = 'var(--accent-green)';
    } catch (e) {
      customHeadersValidation.style.display = 'block';
      customHeadersInput.style.borderColor = 'var(--accent-red)';
    }
  });

  function getLLMConfig() {
    let customHeaders = {};
    const val = customHeadersInput.value.trim();
    if (val) {
      try {
        customHeaders = JSON.parse(val);
      } catch (e) {
        console.error('Invalid custom headers JSON:', e);
      }
    }
    return {
      provider: providerSelect.value,
      apiKey: apiKeyInput.value.trim(),
      baseURL: baseUrlInput.value.trim(),
      modelName: modelNameInput.value.trim(),
      customHeaders: customHeaders
    };
  }

  // --- 3. Git Branch Initialization ---
  gitDevBtn.addEventListener('click', async () => {
    gitStatusLog.innerText = 'Creating dev branch...';
    try {
      const response = await fetch('/api/git/branch', { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        gitStatusLog.innerText = `Branch: dev (${data.message})`;
        gitStatusLog.style.color = '#50fa7b';
      } else {
        gitStatusLog.innerText = `Error: ${data.error}`;
        gitStatusLog.style.color = '#ff5555';
      }
    } catch (err) {
      gitStatusLog.innerText = `Error: ${err.message}`;
      gitStatusLog.style.color = '#ff5555';
    }
  });

  // --- 4. Secrets Scrubbing & Keyup Detection ---
  conceptTextarea.addEventListener('input', async () => {
    const text = conceptTextarea.value;
    if (!text.trim()) {
      redactBanner.classList.add('hidden');
      return;
    }
    
    try {
      const res = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      const data = await res.json();
      if (data.matchedCount > 0) {
        redactBanner.classList.remove('hidden');
      } else {
        redactBanner.classList.add('hidden');
      }
    } catch (err) {
      console.error('Scan error:', err);
    }
  });

  redactAllBtn.addEventListener('click', () => {
    const text = conceptTextarea.value;
    // Perform scrubbing locally or call API
    // Local scrubbing mockup for simple replacements:
    let scrubbed = text
      .replace(/\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b/g, '[REDACTED_IP_ADDRESS]')
      .replace(/\bAKIA[0-9A-Z]{16}\b/g, '[REDACTED_AWS_KEY]')
      .replace(/(?:password|secret)\b\s*[:=]\s*['"]?([a-zA-Z0-9_\-+=/]{6,})['"]?/gi, 'password = "[REDACTED_PASSWORD]"');
      
    conceptTextarea.value = scrubbed;
    redactBanner.classList.add('hidden');
  });

  // --- 5. File Drag & Drop Ingestion ---
  fileDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileDropzone.classList.add('dragover');
  });

  fileDropzone.addEventListener('dragleave', () => {
    fileDropzone.classList.remove('dragover');
  });

  fileDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    fileDropzone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    handleFiles(files);
  });

  fileInput.addEventListener('change', () => {
    handleFiles(fileInput.files);
  });

  function handleFiles(files) {
    for (let file of files) {
      const name = file.name;
      const size = file.size;
      const type = file.type;
      
      const reader = new FileReader();

      // If it's an image
      if (type.startsWith('image/')) {
        reader.onload = (event) => {
          uploadedFiles.push({
            name,
            isImage: true,
            mimeType: type,
            base64Data: event.target.result.split(',')[1] // Extract pure base64
          });
          renderFileChips();
        };
        reader.readAsDataURL(file);
      } else {
        // Read as text by default for csv, md, xml, txt
        reader.onload = (event) => {
          uploadedFiles.push({
            name,
            isImage: false,
            content: event.target.result
          });
          renderFileChips();
          // Append to concept workspace
          conceptTextarea.value += `\n\n--- [Uploaded File Content: ${name}] ---\n${event.target.result}\n`;
          conceptTextarea.dispatchEvent(new Event('input'));
        };
        reader.readAsText(file);
      }
    }
  }

  function renderFileChips() {
    uploadedFilesList.innerHTML = '';
    uploadedFiles.forEach(file => {
      const chip = document.createElement('span');
      chip.className = 'file-chip';
      chip.innerText = `${file.name} ${file.isImage ? '(Image)' : '(Text)'}`;
      uploadedFilesList.appendChild(chip);
    });
  }

  // --- 6. Concept Expansion Generation ---
  expandBtn.addEventListener('click', async () => {
    const concept = conceptTextarea.value.trim();
    if (!concept) return alert('Please enter your concept description or specifications first.');

    expandBtn.innerText = 'Analyzing Spec Breakdown...';
    expandBtn.disabled = true;

    try {
      const images = uploadedFiles.filter(f => f.isImage);
      const res = await fetch('/api/expand', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          concept,
          images,
          config: getLLMConfig()
        })
      });
      const data = await res.json();
      if (data.expandedConcept) {
        expandedConcept = data.expandedConcept;
        // Simple Markdown rendering: replace headers, lists, bold tags
        const html = renderMarkdownToHTML(expandedConcept);
        expandOutputRendered.innerHTML = html;
        expandOutputCard.classList.remove('hidden');
        expandOutputCard.scrollIntoView({ behavior: 'smooth' });

        // Load interview questions
        generateInterviewQuestions();
        
        // Load security scan
        generateSecurityScan();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (err) {
      alert(`Error calling server: ${err.message}`);
    } finally {
      expandBtn.innerText = 'Generate Spec Breakdown';
      expandBtn.disabled = false;
    }
  });

  // Simple parser converting markdown notation to basic HTML blocks
  function renderMarkdownToHTML(md) {
    if (!md) return '';
    return md
      .replace(/^#\s+(.*)$/gm, '<h1>$1</h1>')
      .replace(/^##\s+(.*)$/gm, '<h2>$1</h2>')
      .replace(/^###\s+(.*)$/gm, '<h3>$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/^-\s+(.*)$/gm, '<li>$1</li>')
      .replace(/^\*\s+(.*)$/gm, '<li>$1</li>')
      .replace(/([^>\r\n]?)(\r\n|\n\r|\r|\n)/g, '$1<br>$2');
  }

  // --- 7. Live Editor formatting options ---
  window.formatDoc = (command) => {
    document.execCommand(command, false, null);
  };

  fixHeadingsBtn.addEventListener('click', () => {
    // Normalizes headings capitalization and formats
    let content = expandOutputRendered.innerHTML;
    // Replace lowercase headers to clean headers
    content = content.replace(/<h1>(.*?)<\/h1>/gi, (m, g) => `<h1>${g.toUpperCase()}</h1>`);
    expandOutputRendered.innerHTML = content;
  });

  fixTablesBtn.addEventListener('click', () => {
    // Simple mock to generate clean HTML table formatting out of raw pipe structures
    let content = expandOutputRendered.innerHTML;
    if (content.includes('|')) {
      // Very simple parsing of markdown tables into HTML tables
      const lines = content.split('<br>');
      let tableHtml = '<table border="1" style="border-collapse: collapse; width: 100%;"><tbody>';
      let inTable = false;
      
      const newLines = lines.map(line => {
        if (line.includes('|')) {
          inTable = true;
          const cols = line.split('|').filter(c => c.trim());
          const tr = '<tr>' + cols.map(c => `<td style="padding: 8px;">${c.trim()}</td>`).join('') + '</tr>';
          return tr;
        } else {
          if (inTable) {
            inTable = false;
            return '</tbody></table>' + line;
          }
          return line;
        }
      });
      expandOutputRendered.innerHTML = newLines.join('');
    }
  });

  // --- 8. Scoping Interview Control Flow ---
  async function generateInterviewQuestions() {
    questionsContainer.innerHTML = '<p class="placeholder-text">Loading clarification questions...</p>';
    try {
      const res = await fetch('/api/interview/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          expandedConcept: expandedConcept,
          config: getLLMConfig()
        })
      });
      const data = await res.json();
      if (data.questions) {
        interviewQuestions = data.questions;
        const questionsList = interviewQuestions.split('\n').filter(q => q.match(/^\d+\./));
        
        questionsContainer.innerHTML = '';
        questionsList.forEach((qText, i) => {
          const box = document.createElement('div');
          box.className = 'q-box';
          
          const label = document.createElement('p');
          label.innerText = qText;
          box.appendChild(label);
          
          const input = document.createElement('input');
          input.type = 'text';
          input.className = 'interview-answer-input';
          input.placeholder = 'Type your answer here...';
          box.appendChild(input);
          
          questionsContainer.appendChild(box);
        });

        submitInterviewBtn.classList.remove('hidden');
      }
    } catch (err) {
      questionsContainer.innerHTML = `<p class="placeholder-text" style="color:#ff5555">Error: ${err.message}</p>`;
    }
  }

  submitInterviewBtn.addEventListener('click', async () => {
    const boxes = document.querySelectorAll('.q-box');
    const answers = [];
    boxes.forEach(box => {
      const q = box.querySelector('p').innerText;
      const a = box.querySelector('input').value;
      answers.push({ question: q, answer: a });
    });

    submitInterviewBtn.innerText = 'Compiling Master Prompt...';
    
    // Call Generate Master Prompt
    try {
      const res = await fetch('/api/prompt/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          concept: conceptTextarea.value,
          interviewAnswers: JSON.stringify(answers),
          vulnerabilities: securityVulnerabilities,
          config: getLLMConfig()
        })
      });
      const data = await res.json();
      if (data.masterPrompt) {
        masterPrompt = data.masterPrompt;
        promptWorkspace.value = masterPrompt;
        alert('Master Prompt compiled successfully! Review in Tab 5.');
      }
    } catch (err) {
      alert(`Error compiling prompt: ${err.message}`);
    } finally {
      submitInterviewBtn.innerText = 'Submit Answers';
    }
  });

  // --- 9. Security Auditor checks ---
  async function generateSecurityScan() {
    securityContent.innerHTML = '<p class="placeholder-text">Running vulnerability scanner...</p>';
    try {
      const res = await fetch('/api/analyze/vulnerabilities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          concept: conceptTextarea.value,
          config: getLLMConfig()
        })
      });
      const data = await res.json();
      if (data.vulnerabilities) {
        securityVulnerabilities = data.vulnerabilities;
        securityContent.innerHTML = renderMarkdownToHTML(securityVulnerabilities);
      }
    } catch (err) {
      securityContent.innerHTML = `<p class="placeholder-text" style="color:#ff5555">Error: ${err.message}</p>`;
    }
  }

  // --- 10. Programming Language Code syntax checker ---
  checkSyntaxBtn.addEventListener('click', async () => {
    const code = syntaxCodeArea.value.trim();
    const language = syntaxLangSelect.value;
    
    if (!code) return alert('Please paste some code to validate first.');

    checkSyntaxBtn.innerText = 'Checking Syntax...';
    syntaxResultAlert.className = 'alert hidden';

    try {
      const res = await fetch('/api/syntax/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language })
      });
      const data = await res.json();
      
      if (data.success) {
        syntaxResultAlert.innerText = data.message;
        syntaxResultAlert.className = 'alert alert-success';
      } else {
        syntaxResultAlert.innerText = `Syntax Error: ${data.error}`;
        syntaxResultAlert.className = 'alert alert-danger';
      }
    } catch (err) {
      syntaxResultAlert.innerText = `System Validation error: ${err.message}`;
      syntaxResultAlert.className = 'alert alert-danger';
    } finally {
      checkSyntaxBtn.innerText = 'Validate Syntax';
    }
  });

  // --- 11. Conversational Prompt tuning panel ---
  chatSendBtn.addEventListener('click', async () => {
    const input = chatInput.value.trim();
    if (!input) return;

    // Render user message
    const uMsg = document.createElement('div');
    uMsg.className = 'message user';
    uMsg.innerText = input;
    chatMessagesContainer.appendChild(uMsg);
    chatInput.value = '';

    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message system';
    loadingMsg.innerText = 'Optimizing system instructions...';
    chatMessagesContainer.appendChild(loadingMsg);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;

    try {
      const res = await fetch('/api/prompt/tune', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          currentPrompt: promptWorkspace.value,
          tuningInstruction: input,
          config: getLLMConfig()
        })
      });
      const data = await res.json();
      if (data.tunedPrompt) {
        masterPrompt = data.tunedPrompt;
        promptWorkspace.value = masterPrompt;
        
        loadingMsg.innerText = 'Draft prompt updated successfully!';
      }
    } catch (err) {
      loadingMsg.innerText = `Tuning failed: ${err.message}`;
    }
  });

  // --- 12. Multi-Format Exporter Panel ---
  exportBtn.addEventListener('click', async () => {
    const content = promptWorkspace.value || conceptTextarea.value;
    const format = exportFormatSelect.value;
    
    if (!content) return alert('Workspace is empty. Generate content to export first.');

    try {
      const response = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content,
          format,
          docName: 'master-scoping-prompt'
        })
      });

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `master-scoping-prompt.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    }
  });

  // --- 13. Accept / Discard Change Lifecycle Actions ---
  acceptExpandBtn.addEventListener('click', () => {
    expandedConcept = expandOutputRendered.innerText;
    alert('Specification accepted and locked into active workspace.');
    // In a real flow, this could auto-commit files on the local git branch
  });

  regenerateExpandBtn.addEventListener('click', () => {
    uploadedFiles = [];
    renderFileChips();
    expandBtn.click(); // Re-trigger LLM expansion
  });

  discardExpandBtn.addEventListener('click', () => {
    expandOutputRendered.innerHTML = '';
    expandOutputCard.classList.add('hidden');
    alert('Workspace modifications discarded.');
  });

});
