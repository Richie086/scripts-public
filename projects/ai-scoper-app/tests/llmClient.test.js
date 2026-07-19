const axios = require('axios');
const LLMClient = require('../llmClient');

jest.mock('axios');

describe('LLMClient Custom Headers & Config', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('callInternal forwards custom headers to baseURL', async () => {
    axios.post.mockResolvedValue({
      data: {
        choices: [{ message: { content: 'Simulated response content' } }]
      }
    });

    const client = new LLMClient({
      provider: 'internal',
      baseURL: 'http://my-local-ollama:11434/v1/chat/completions',
      modelName: 'llama3',
      customHeaders: {
        'X-Routing-Key': 'key-value-123',
        'X-Custom-Auth': 'secret-auth-token'
      }
    });

    const result = await client.generateContent('Hello Ollama');

    expect(result).toBe('Simulated response content');
    expect(axios.post).toHaveBeenCalledTimes(1);
    expect(axios.post).toHaveBeenCalledWith(
      'http://my-local-ollama:11434/v1/chat/completions',
      expect.any(Object),
      expect.objectContaining({
        headers: {
          'X-Routing-Key': 'key-value-123',
          'X-Custom-Auth': 'secret-auth-token'
        }
      })
    );
  });

  test('callInternal combines apiKey Authorization header with customHeaders', async () => {
    axios.post.mockResolvedValue({
      data: {
        choices: [{ message: { content: 'Authenticated response' } }]
      }
    });

    const client = new LLMClient({
      provider: 'internal',
      apiKey: 'my-custom-key',
      customHeaders: {
        'X-Custom-Auth': 'secret-auth-token'
      }
    });

    await client.generateContent('Auth test');

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:11434/v1/chat/completions',
      expect.any(Object),
      expect.objectContaining({
        headers: {
          'X-Custom-Auth': 'secret-auth-token',
          'Authorization': 'Bearer my-custom-key'
        }
      })
    );
  });
});
