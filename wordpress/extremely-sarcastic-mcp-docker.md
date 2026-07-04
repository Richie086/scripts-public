# The Absolute Joy of Modern Dev Tools: How I Spent My Weekend Begging Docker and Antigravity to Talk to Each Other

Oh, modern software development. What a time to be alive. Gone are the days of writing code and running it. Instead, we now get to spend our beautiful, fleeting weekends configuring containerized micro-agents, playing referee between Unix sockets, and debugging state managers for tools that are supposedly designed to replace us.

If you, too, have had the distinct privilege of trying to connect a containerized Model Context Protocol (MCP) server to Google Antigravity, you’ve probably enjoyed the double-feature horror show of a `/var/run/docker.sock` permission denial followed immediately by a gorgeous, unhandled `TypeError: Cannot read properties of null (reading '__store')` UI crash. 

Here is my completely serious, not-at-all-bitter guide to fixing these two monumental achievements in user-experience design.

---

## Phase 1: The Secure and User-Friendly World of Docker Sockets

First, my newly minted MCP server needed to communicate with the Docker daemon. Naturally, Docker—acting with the defensive paranoia of a medieval castle guard—slammed the door in my face. Permission denied.

The textbook solution, written by people who clearly live in a utopia, is to simply add yourself to the `docker` group:

```bash
sudo usermod -aG docker $USER
```

### The "Command Not Found" Masterpiece

In a normal world, you’d run `newgrp docker` and go about your day. But because I was working in a beautifully minimalist modern environment, my terminal greeted me with the helpful message: `newgrp: command not found`. Because why would a shell include basic Unix utilities? That would be too convenient.

If you find yourself trapped in this same developer paradise, here are the highly efficient hoops I had to jump through:

* **The Virtual Rage Quit**: Close your IDE, close your terminal, close your laptop, walk away, and open a fresh session.
* **The Password Interrogation**: Run `su - $USER` and type your password just to convince your own machine that you are, in fact, yourself.
* **The "Security is an Illusion" Bypass**: If your environment refuses to propagate group permissions, you can just take ownership of the socket file yourself:
  ```bash
  sudo chown $USER /var/run/docker.sock
  ```

> [!TIP]
> Changing the socket ownership is a fantastic way to bypass permissions. Sure, security purists will weep about exposing your entire host system, but who cares? It works, and that’s a problem for Monday. Just whatever you do, don't run `chmod 777` unless you want to invite the entire internet into your socket.

---

## Phase 2: The Antigravity Settings UI — A Triumph of Engineering

Once the Docker permissions were resolved, I prepared myself for the seamless, AI-driven future. I opened the Antigravity Settings panel. 

And then, *bam*.

```
TypeError: Cannot read properties of null (reading '__store')
```

Absolute perfection. A cutting-edge AI coding assistant whose configuration GUI literally cannot handle the load of its own configuration data. It’s poetic, really. The tool built to automate programming was defeated by a null pointer.

Since the graphical interface was now serving as a very expensive screen saver, I had to configure this futuristic AI GUI the old-fashioned way: by writing raw JSON in a terminal.

### Step 1: Edit the JSON by Hand (Like the Future Intended)

Forget the settings panel. Open up your favorite terminal text editor:

```bash
nano ~/.gemini/config/mcp_config.json
```

### Step 2: Inject the Secret Formula

If the config file is empty (or even if it isn't), paste this block in. Make sure to replace `YOUR_FINE_GRAINED_GITHUB_TOKEN` with your actual token—which you definitely kept safe and didn't accidentally commit to public git repository:

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        "ghcr.io/modelcontextprotocol/servers/github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_FINE_GRAINED_GITHUB_TOKEN"
      }
    }
  }
}
```

### Step 3: Nuke the UI Cache

To convince the Antigravity client to stop throwing tantrums about `__store` being null, you have to manually delete its brain. Run this in your terminal to delete the local storage database:

```bash
rm -rf ~/.config/Antigravity/Local\ Storage
```

Because nothing says "advanced developer experience" quite like using `rm -rf` to fix a settings menu.

### Step 4: Act Like Nothing Happened

Now, restart Antigravity. To verify the server is actually working without touching the cursed Settings menu (which you should never open again), open the Agentic Panel (`Ctrl + Alt + B`) and type this prompt:

> "Please check your connection to the GitHub MCP server and list my available repositories."

And just like magic, the AI will bypass its own broken UI, read the mounted socket file, and fetch your repositories. 

So there you have it. AI is definitely replacing all of us next week—just as soon as someone figures out how to render a settings page without crashing the state manager.
