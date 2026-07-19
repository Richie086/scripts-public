(() => {
  const modal = document.getElementById("fs-browser-modal");
  if (!modal) return;

  const listEl = document.getElementById("fs-browser-list");
  const pathEl = document.getElementById("fs-browser-path");
  const errEl = document.getElementById("fs-browser-error");
  const rootSelect = document.getElementById("fs-browser-root");
  const targetInput = document.getElementById("url");
  let currentPath = "";
  let selected = null;

  function showError(msg) {
    errEl.textContent = msg || "";
    errEl.hidden = !msg;
  }

  async function load(path) {
    showError("");
    selected = null;
    const url = new URL("/api/fs/list", window.location.origin);
    if (path) url.searchParams.set("path", path);
    const resp = await fetch(url, { credentials: "same-origin" });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      showError(data.error || "Failed to list directory");
      return;
    }
    currentPath = data.path;
    pathEl.textContent = data.path;
    listEl.innerHTML = "";
    if (data.parent) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.innerHTML = `<span>../</span><span class="fs-kind">up</span>`;
      btn.addEventListener("click", () => load(data.parent));
      li.appendChild(btn);
      listEl.appendChild(li);
    }
    for (const entry of data.entries || []) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.innerHTML = `<span>${entry.name}${entry.type === "dir" ? "/" : ""}</span><span class="fs-kind">${entry.type}</span>`;
      btn.addEventListener("click", () => {
        if (entry.type === "dir") {
          load(entry.path);
        } else {
          selected = entry;
          listEl.querySelectorAll("button").forEach((b) => b.classList.remove("is-selected"));
          btn.classList.add("is-selected");
        }
      });
      btn.addEventListener("dblclick", () => {
        if (entry.type === "dir") load(entry.path);
        else usePath(entry.path);
      });
      li.appendChild(btn);
      listEl.appendChild(li);
    }
  }

  function openModal() {
    modal.hidden = false;
    const root = rootSelect?.value;
    load(root || "");
  }

  function closeModal() {
    modal.hidden = true;
  }

  function usePath(path) {
    if (!targetInput || !path) return;
    targetInput.value = path;
    closeModal();
  }

  document.querySelectorAll("[data-fs-browse]").forEach((btn) => {
    btn.addEventListener("click", openModal);
  });
  document.getElementById("fs-browser-close")?.addEventListener("click", closeModal);
  document.getElementById("fs-browser-cancel")?.addEventListener("click", closeModal);
  document.getElementById("fs-browser-use-folder")?.addEventListener("click", () => usePath(currentPath));
  document.getElementById("fs-browser-use-file")?.addEventListener("click", () => {
    if (selected) usePath(selected.path);
    else showError("Select a file first (single-click).");
  });
  rootSelect?.addEventListener("change", () => load(rootSelect.value));
  modal.addEventListener("click", (ev) => {
    if (ev.target === modal) closeModal();
  });
})();
