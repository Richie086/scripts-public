(() => {
  const KEY = "ideaforge-theme";
  const root = document.documentElement;

  function preferred() {
    const saved = localStorage.getItem(KEY);
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function apply(theme) {
    root.setAttribute("data-theme", theme);
    const light = document.getElementById("gh-md-light");
    const dark = document.getElementById("gh-md-dark");
    if (light && dark) {
      light.disabled = theme !== "light";
      dark.disabled = theme !== "dark";
    }
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
      btn.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
      btn.textContent = theme === "dark" ? "Light" : "Dark";
    });
  }

  apply(preferred());

  document.addEventListener("click", (ev) => {
    const toggle = ev.target.closest("[data-theme-toggle]");
    if (toggle) {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      localStorage.setItem(KEY, next);
      apply(next);
      return;
    }
    const dropBtn = ev.target.closest("[data-nav-more]");
    const drop = document.querySelector(".nav-dropdown");
    if (dropBtn && drop) {
      drop.classList.toggle("open");
      return;
    }
    if (drop && !ev.target.closest(".nav-dropdown")) {
      drop.classList.remove("open");
    }
  });
})();
