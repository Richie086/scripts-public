class SecurityScanner {
  constructor() {
    this.patterns = {
      // 1. PII
      email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
      ssn: /\b\d{3}-\d{2}-\d{4}\b/g,
      phone: /\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,

      // 2. Networking Configurations
      ip_address: /\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/g,
      mac_address: /\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b/g,
      hostname: /\b[a-zA-Z0-9-]+\.(?:local|lan|internal|home|onload)\b/g,

      // 3. Credentials & Secrets
      aws_key: /\bAKIA[0-9A-Z]{16}\b/g,
      aws_secret: /\b[a-zA-Z0-9+/]{40}\b/g,
      private_key: /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g,
      api_key: /(?:api[_-]?key|access[_-]?token|auth[_-]?token|bearer|client[_-]?secret|password|passwd|secret)\b\s*[:=]\s*['"]?([a-zA-Z0-9_\-+=/]{12,})['"]?/gi
    };
  }

  /**
   * Scans text input for sensitive content.
   * Returns list of vulnerabilities and flags.
   */
  scan(text) {
    if (!text || typeof text !== 'string') {
      return { vulnerabilities: [], matchedCount: 0 };
    }

    const vulnerabilities = [];
    let matchedCount = 0;

    for (const [key, regex] of Object.entries(this.patterns)) {
      // Reset regex index
      regex.lastIndex = 0;
      let match;

      while ((match = regex.exec(text)) !== null) {
        matchedCount++;
        const token = match[0];
        
        // Severity mapping
        let severity = 'MEDIUM';
        if (key === 'aws_key' || key === 'private_key' || key === 'aws_secret' || key === 'api_key') {
          severity = 'HIGH';
        } else if (key === 'email' || key === 'phone') {
          severity = 'LOW';
        }

        vulnerabilities.push({
          type: key.toUpperCase(),
          token: token,
          index: match.index,
          severity: severity,
          description: `Detected potential sensitive ${key.replace('_', ' ')}: "${token.substring(0, 15)}..."`
        });
      }
    }

    return {
      vulnerabilities,
      matchedCount
    };
  }

  /**
   * Automatically scrubs / replaces sensitive tokens in the input text.
   */
  scrub(text, customRedactedTokens = []) {
    if (!text || typeof text !== 'string') return text;

    let scrubbedText = text;

    // First replace generic patterns
    for (const [key, regex] of Object.entries(this.patterns)) {
      regex.lastIndex = 0;
      scrubbedText = scrubbedText.replace(regex, (match) => {
        return `[REDACTED_${key.toUpperCase()}]`;
      });
    }

    // Replace custom matched tokens explicitly
    for (const token of customRedactedTokens) {
      const escapedToken = token.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
      const tokenRegex = new RegExp(escapedToken, 'g');
      scrubbedText = scrubbedText.replace(tokenRegex, '[REDACTED_CUSTOM]');
    }

    return scrubbedText;
  }
}

module.exports = SecurityScanner;
