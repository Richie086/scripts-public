Visual Studio Code (VSCode) has become the go-to code editor for developers worldwide. It's lightweight, incredibly customizable, and supports a massive ecosystem of extensions. Whether you are a seasoned software engineer or just starting your coding journey, VSCode is an excellent choice.

In this guide, we will walk you through the steps to install Visual Studio Code on Windows, macOS, and Linux.

---

## Installing VSCode on Windows

Installing VSCode on Windows is straightforward thanks to the official installer provided by Microsoft.

### Method 1: Using the Official Installer (Recommended)

1. **Download the Installer:**
   Navigate to the official [VSCode download page](https://code.visualstudio.com/Download) and click on the **Windows** button to download the User Installer (recommended for most users).

2. **Run the Installer:**
   Once the download is complete, locate the downloaded `.exe` file (usually in your Downloads folder) and double-click it to run the installer.

3. **Follow the Setup Wizard:**
   - **Accept the License Agreement.**
   - **Select Destination Location:** You can usually leave this as the default.
   - **Select Additional Tasks:** This is important! We highly recommend checking the boxes for:
     - **"Add 'Open with Code' action to Windows Explorer file context menu"**
     - **"Add 'Open with Code' action to Windows Explorer directory context menu"**
     - **"Register Code as an editor for supported file types"**
     - **"Add to PATH (requires shell restart)"** (Crucial for running VSCode from the command line).
   - Click **Install**.

4. **Launch VSCode:**
   Once the installation is finished, check "Launch Visual Studio Code" and click **Finish**.

### Method 2: Using the Windows Package Manager (winget)

If you prefer using the command line, you can install VSCode using `winget`. Open PowerShell or Command Prompt and run:

```powershell
winget install -e --id Microsoft.VisualStudioCode
```

---

## Installing VSCode on macOS

For Mac users, installing VSCode is as simple as dragging an app into your Applications folder.

### Method 1: Standard Installation

1. **Download the Archive:**
   Go to the [VSCode download page](https://code.visualstudio.com/Download) and click on the **Mac** button. This will download a `.zip` file containing the application.

2. **Extract the Application:**
   Double-click the downloaded `.zip` file to extract its contents. You should now see the "Visual Studio Code" application.

3. **Move to Applications Folder:**
   Drag the "Visual Studio Code" application into your **Applications** folder to make it available in your Launchpad.

4. **Launch VSCode:**
   Open Launchpad or Finder, navigate to Applications, and double-click Visual Studio Code. (You may see a warning that it's an app downloaded from the internet; click "Open").

### Method 2: Using Homebrew (For Terminal Users)

If you use Homebrew, the popular package manager for macOS, you can install VSCode via Homebrew Cask. Open your terminal and run:

```bash
brew install --cask visual-studio-code
```

---

## Installing VSCode on Linux

Linux distributions vary, so the installation method depends on the package manager your system uses. We'll cover Debian/Ubuntu-based and Red Hat/Fedora/SUSE-based distributions, as well as the Snap store.

### Method 1: Snap Package (Easiest for Many Distros)

If your Linux distribution supports Snaps (like Ubuntu), this is the easiest way to get the latest version. Open your terminal and run:

```bash
sudo snap install --classic code
```

### Method 2: Debian/Ubuntu (APT)

For Debian, Ubuntu, Linux Mint, and similar distributions, use the official Microsoft repository.

1. **Update packages and install dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install wget gpg
   ```

2. **Import the Microsoft GPG key:**
   ```bash
   wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
   sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
   ```

3. **Add the VSCode repository:**
   ```bash
   echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" |sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
   ```

4. **Install VSCode:**
   ```bash
   sudo apt-get install apt-transport-https
   sudo apt-get update
   sudo apt-get install code
   ```

### Method 3: Red Hat/Fedora/CentOS (YUM/DNF)

For RHEL, Fedora, CentOS, and similar systems:

1. **Import the Microsoft GPG key and add the repository:**
   ```bash
   sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
   sudo sh -c 'echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo'
   ```

2. **Install VSCode (using DNF on Fedora/RHEL 8+):**
   ```bash
   sudo dnf check-update
   sudo dnf install code
   ```
   *(Alternatively, use `yum` instead of `dnf` on older systems).*

---

## Installing Extensions

One of VSCode's greatest strengths is its massive extension marketplace.

1. **Open the Extensions View:** Click on the Extensions icon on the left Activity Bar (it looks like four squares) or press `Ctrl+Shift+X` (`Cmd+Shift+X` on macOS).
2. **Search:** In the search bar at the top, type the name of the extension or language you want (e.g., "Python", "Prettier", "Live Server").
3. **Install:** Click the **Install** button next to the extension you want. It will install and activate instantly—no restart required in most cases!

---

## Working with GitHub

VSCode has excellent built-in support for Git and GitHub, making version control seamless.

1. **Initialize a Repository:** If your project isn't already a Git repository, you can initialize one by clicking the **Source Control** icon on the Activity Bar (it looks like a branching graph) and clicking **Initialize Repository**.
2. **Stage and Commit:** Make changes to your files, then go to the Source Control view. Click the `+` icon next to files to stage them, type a commit message in the text box, and click the **Commit** button (or checkmark icon).
3. **Connect to GitHub:** 
   - To push your code, click the **Publish Branch** button (or the Sync icon in the bottom status bar).
   - VSCode will prompt you to sign in to GitHub if you haven't already. Follow the browser prompts to authenticate.
   - You can choose to publish to a public or private repository directly from the editor.
4. **Pull Requests and Issues:** For even deeper integration, install the official **GitHub Pull Requests and Issues** extension. This allows you to review PRs, comment on code, and manage issues without ever leaving VSCode!

---

## Next Steps

Now that you have Visual Studio Code installed, extended, and connected to GitHub, you're ready to start coding! Here are a few quick tips to get you started:

- **Open a Folder:** Go to `File > Open Folder...` to open your project directory and start working on your code.
- **Use the Integrated Terminal:** Press `Ctrl+` ` (backtick) or go to `Terminal > New Terminal` to open a command line right inside VSCode.

Happy coding!
