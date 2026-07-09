# Stop Typing the Same Command 50 Times: Introducing the Alias & Function Suggester

Oh, developers. We are a special breed. We will happily spend six hours writing, testing, and debugging a complex script to automate a task that takes exactly five seconds. It is a fundamental law of software engineering: if you can avoid typing three extra characters, no amount of time spent coding is too high a price to pay.

Which brings me to my latest achievement in productivity optimization (or extreme laziness, depending on how you look at it): **`suggest_aliases.py`**.

If you've spent years in the terminal, you probably have a `.bashrc` or `.bash_aliases` file that is an absolute graveyard of half-remembered shortcuts. But are they the *right* shortcuts? Do they match what you *actually* type every day, or are they just artifacts of whatever project you were obsessed with back in 2024?

Instead of guessing, I built a Python utility that performs statistical frequency analysis on your shell history, weighs your commands by recency, and automatically suggests the exact aliases and custom shell functions you should add to save your precious keystrokes.

---

## The Core Concept: Listening to Your Shell History

The script reads your `~/.bash_history` (or whatever history file you point it to). But simple frequency counts are dumb. If you ran `make clean` 500 times during a hectic weekend project three months ago, but haven't touched it since, you don't need an alias for it today.

To solve this, the script implements **Recency Weighting**:
- Commands typed in the most recent 1/3 of your history get a **2.0x multiplier**.
- Commands in the middle 1/3 get a **1.5x multiplier**.
- Commands in the oldest 1/3 get a **1.0x multiplier**.

This guarantees that the aliases suggested actually reflect your *current* workflows, not your historical debugging sessions.

---

## Feature 1: The "Service Suite" Generator

If you manage web servers, database clusters, or system daemons, you know the drill. You start a service, check its status, restart it when it breaks, and tail the journal logs. That's four distinct, verbose commands:

```bash
sudo systemctl start apache2
sudo systemctl status apache2
sudo systemctl restart apache2
sudo journalctl -xeu apache2
```

`suggest_aliases.py` detects these patterns. If it sees you interacting with a service, it doesn't suggest one alias—it suggests a complete **Service Suite** of short commands:

```bash
alias apache-start='sudo systemctl start apache2'
alias apache-stop='sudo systemctl stop apache2'
alias apache-restart='sudo systemctl restart apache2'
alias apache-status='sudo systemctl status apache2'
alias apache-journalctl='sudo journalctl -xeu apache2'
```

Instantly, four long-winded commands become readable, concise keystrokes.

---

## Feature 2: Automatic Function Projections (The `mkcd` Builder)

Some command sequences are inseparable. The classic example is creating a directory and immediately navigating into it:

```bash
mkdir my-new-project
cd my-new-project
```

An alias can't handle this dynamically because it needs to pass the directory name to both commands. You need a shell function. 

The script parses your history for these consecutive `mkdir` and `cd` pairs. When it detects them, it proposes injecting a custom shell function directly into your configuration:

```bash
mkcd() {
    mkdir -p "$1" && cd "$1"
}
```

Now, instead of typing two commands and repeating the directory name, you just type `mkcd my-new-project` and get on with your life.

---

## Feature 3: Safety and Sourcing Verification

Modifying system shell files is always a bit nerve-wracking. To keep your system safe, the script follows two core rules:

1. **Dry-Run by Default**: Unless you explicitly run with `--apply` or `--interactive`, the script will only output a beautifully formatted Markdown table of its findings. It won't touch a single file on your disk.
2. **Sourcing Verification**: If you do choose to apply the recommendations, the script will verify if your `~/.bashrc` actually sources `~/.bash_aliases`. If it doesn't, it will ask for permission, back up your files, and safely append the sourcing snippet so your new aliases actually load on startup.

---

## How to Get It

You can download and run the script directly from my public scripts repository:

```bash
# Download the script
curl -s -o suggest_aliases.py https://raw.githubusercontent.com/Richie086/scripts-public/main/python/suggest_aliases.py

# Run a safe dry-run scan
python3 suggest_aliases.py
```

If you want to review the full options (such as custom thresholds, history file paths, or run in interactive installation mode), just pass the help flag:

```bash
python3 suggest_aliases.py --help
```

You can view the full source code and documentation at the [scripts-public GitHub repository](https://github.com/Richie086/scripts-public).

Stop wasting time typing raw system commands. Spend five minutes setting up these aliases, and save yourself literally seconds of typing every single day!
