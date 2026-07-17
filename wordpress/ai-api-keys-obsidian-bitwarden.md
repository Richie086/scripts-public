Why pay $20 a month for a web interface that treats you like a child, puts you on a timer, and hides the "real" models behind a paywall when you can just buy tokens in bulk for fractions of a penny and run them in your own local applications? 

Welcome to the world of API keys—the developer equivalent of bypassing the ticket booth and walking straight into the VIP lounge. 

If you are looking for the perfect landing pad for these keys, look no further than **Obsidian**. It’s a local-first, plain-text markdown vault. By connecting Obsidian directly to AI models via APIs, you get an infinitely customizable assistant that only bills you for what you actually use.

But this isn't just about saving money. Using an LLM inside a local, plain-text markdown application is **god mode** for managing your ideas. Because markdown is open and plain-text:
*   **You own your data**: No proprietary database, no vendor lock-in. If Obsidian disappears tomorrow, your notes remain clean, human-readable text files.
*   **Easy Git Revisioning**: Every edit, rewrite, and AI-generated summary can be tracked chronologically using Git. You get a perfect history of how your ideas evolved.
*   **Seamless Syncing**: You can sync plain-text folders between your phone, laptop, and coworkers using iCloud, Git, Syncthing, or simple cron jobs.
*   **Uniform Formatting**: You can have the LLM enforce strict markdown formatting, ensuring your docs are clean, readable, and ready for developers or publishing platforms.

Here is how to install Obsidian on any operating system, generate your API keys, and organize them in Bitwarden so you don't end up with credential chaos.

---

## Part 1: Installing Obsidian on Any OS

Before we get the keys, we need the lock. Obsidian runs on virtually anything with a screen:

*   **Windows & macOS**: Go to the official [Obsidian Download page](https://obsidian.md/download), grab the installer, and run it. Simple, standard, no surprises.
*   **Linux**: If you're on Linux, you have options:
    *   **Flatpak (Recommended)**: Run `flatpak install flathub md.obsidian.Obsidian`
    *   **Snap**: Run `sudo snap install obsidian --classic`
    *   **AppImage**: Download the AppImage from their site, make it executable (`chmod +x`), and run it directly.
*   **Mobile (iOS & Android)**: Search for "Obsidian" in the Apple App Store or Google Play Store. It runs fully locally on your phone, and you can sync it using Git, iCloud, or Obsidian Sync.

---

## Part 2: Step-by-Step API Key Generation (Bypassing the UIs)

To get these models to talk to your local applications, you need an API key. This is a secret string of text that tells the provider's servers to process your requests and bill your card. 

### 1. Google Gemini (Google AI Studio)
Google makes this surprisingly easy (and free, within generous rate limits).
1.  Go to [Google AI Studio](https://aistudio.google.com/).
2.  Log in with your Google account.
3.  Click the **"Get API key"** button in the top left.
4.  Click **"Create API key"** and choose to associate it with a Google Cloud project.
5.  Copy that key immediately. (Google won't show it to you again, because security).

### 2. Anthropic Claude (Anthropic Console)
Anthropic is slightly more developer-focused, but still straightforward.
1.  Go to the [Anthropic Console](https://console.anthropic.com/).
2.  Create an account or sign in.
3.  Navigate to **API Keys** on the dashboard.
4.  Click **"Create Key"**, name it (e.g., "Obsidian Integration"), and copy the generated key.
5.  *Note:* You'll need to fund your account with a minimum of $5 before the key will actually answer your prompts.

### 3. OpenAI (OpenAI Platform)
OpenAI’s dashboard is the blueprint that every other provider copied.
1.  Go to the [OpenAI Platform](https://platform.openai.com/).
2.  Sign in and head to **Dashboard > API Keys** (or click the key icon on the left sidebar).
3.  Click **"Create new secret key"**.
4.  Name it, choose your permissions, and copy it.
5.  Like Anthropic, you must add a billing method and load a few dollars into your balance first.

---

## Part 3: Managing Key Sprawl in Bitwarden (The Golden Rule)

Here’s the catch: once you start generating API keys, they will multiply. You’ll have a key for Obsidian on your desktop, another for Obsidian on your phone, one for a Python script you ran once on a Tuesday, and another for a Discord bot you abandoned. 

Worse, providers will occasionally email you saying: *"Your key sk-proj-... has expired."* If you just dumped these in a text file or in your plugin configs, you will have no idea which key is which, what application it belongs to, or when you made it.

To keep your sanity, manage them in **Bitwarden** using this exact, strict organization formula:

1.  Open your Bitwarden Vault.
2.  Create or edit an entry for your API credentials (e.g., a secure note or login item called "Developer API Keys").
3.  Scroll down to the **Custom Fields** section.
4.  Change the field type dropdown to **Hidden**. (This is critical: it prevents the key from being visible on screen or copied accidentally during screen shares).
5.  Name the field using this exact naming convention:
    ```
    API Key for $PROVIDER $APPLICATION $DATE
    ```
    *   **$PROVIDER**: Gemini, Anthropic, OpenAI, etc.
    *   **$APPLICATION**: Obsidian, PythonScript, Chatbox, etc.
    *   **$DATE**: The date you created/rotated the key (e.g., YYYY-MM-DD).

For example:
*   `API Key for OpenAI Obsidian 2026-07-17`
*   `API Key for Gemini DesktopCopilot 2026-07-17`
*   `API Key for Anthropic TranslationScript 2026-07-17`

6.  Paste the API key into the value field.

By naming your fields this way, you can search your Bitwarden vault for "Obsidian" or "2026" or "OpenAI" and instantly find the exact key, know when it was minted, what application depends on it, and whether it’s time to rotate or delete it. No more guessing which key is which, and no more leaving active credentials scattered across config files.
