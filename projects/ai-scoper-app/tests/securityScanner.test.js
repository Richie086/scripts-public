const SecurityScanner = require('../securityScanner');

describe('Security and PII Scanner Module', () => {
  let scanner;

  beforeEach(() => {
    scanner = new SecurityScanner();
  });

  test('detects email addresses and SSNs', () => {
    const text = 'Contact us at dev-test@my-domain.com or SSN 000-12-3456.';
    const results = scanner.scan(text);

    expect(results.matchedCount).toBe(2);
    const types = results.vulnerabilities.map(v => v.type);
    expect(types).toContain('EMAIL');
    expect(types).toContain('SSN');
  });

  test('detects public and private IP addresses', () => {
    const text = 'Connecting to database server at 192.168.1.80 or 10.0.0.5';
    const results = scanner.scan(text);

    expect(results.matchedCount).toBe(2);
    expect(results.vulnerabilities[0].type).toBe('IP_ADDRESS');
    expect(results.vulnerabilities[0].token).toBe('192.168.1.80');
  });

  test('detects API secrets and keys', () => {
    const text = 'AWS_KEY=AKIA1234567890ABCDEF, api_key: "mySecretApiKeyTokenValue"';
    const results = scanner.scan(text);

    expect(results.matchedCount).toBe(2);
    const types = results.vulnerabilities.map(v => v.type);
    expect(types).toContain('AWS_KEY');
    expect(types).toContain('API_KEY');
  });

  test('scrubs credentials and replaces with placeholders', () => {
    const text = 'Deploy database to 192.168.1.80 and use password = "mySecretPasswordKey".';
    const scrubbed = scanner.scrub(text);

    expect(scrubbed).toContain('[REDACTED_IP_ADDRESS]');
    expect(scrubbed).toContain('[REDACTED_API_KEY]');
    expect(scrubbed).not.toContain('192.168.1.80');
    expect(scrubbed).not.toContain('mySecretPasswordKey');
  });
});
