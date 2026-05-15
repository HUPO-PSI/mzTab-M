(function () {
  const MODE_KEY = "antora-theme-mode";
  const LEGACY_KEY = "antora-theme";
  const html = document.documentElement;
  const darkThemeClass = "dark-theme";

  function getMode() {
    const m = localStorage.getItem(MODE_KEY);
    if (m === "system" || m === "dark" || m === "light") return m;
    const leg = localStorage.getItem(LEGACY_KEY);
    if (leg === "dark" || leg === "light") {
      localStorage.setItem(MODE_KEY, leg);
      localStorage.removeItem(LEGACY_KEY);
      return leg;
    }
    return "system";
  }

  function applyVisibleTheme() {
    const mode = getMode();
    let useDark;
    if (mode === "system") {
      useDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    } else {
      useDark = mode === "dark";
    }
    if (useDark) {
      html.classList.add(darkThemeClass);
    } else {
      html.classList.remove(darkThemeClass);
    }
    updateToggleLabel();
  }

  function setMode(next) {
    if (next === "system") {
      localStorage.setItem(MODE_KEY, "system");
    } else {
      localStorage.setItem(MODE_KEY, next);
    }
    applyVisibleTheme();
  }

  function isDark() {
    return html.classList.contains(darkThemeClass);
  }

  function updateToggleLabel() {
    const toggle = document.getElementById("theme-toggle");
    if (!toggle) return;
    if (isDark()) {
      toggle.innerHTML =
        '<svg class="theme-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
      toggle.setAttribute("aria-label", "Switch to light mode");
    } else {
      toggle.innerHTML =
        '<svg class="theme-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
      toggle.setAttribute("aria-label", "Switch to dark mode");
    }
  }

  function toggleTheme() {
    setMode(isDark() ? "light" : "dark");
    const toggle = document.getElementById("theme-toggle");
    if (toggle) toggle.blur();
  }

  function onSystemThemeChange() {
    const mode = getMode();
    if (mode === "system") {
      applyVisibleTheme();
    } else {
      setMode("system");
    }
  }

  function applyInitialTheme() {
    applyVisibleTheme();
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (typeof mq.addEventListener === "function") {
      mq.addEventListener("change", onSystemThemeChange);
    } else {
      mq.addListener(onSystemThemeChange);
    }
  }

  function ensureToggleButton() {
    const existingToggle = document.getElementById("theme-toggle");
    if (existingToggle) {
      existingToggle.classList.add("adt-header-icon-btn");
      existingToggle.addEventListener("click", toggleTheme);
      updateToggleLabel();
      return;
    }

    const navbarEnd = document.querySelector(".navbar .navbar-end");
    if (!navbarEnd) return;

    const button = document.createElement("button");
    button.id = "theme-toggle";
    button.className = "navbar-item adt-header-icon-btn theme-toggle";
    button.type = "button";
    button.addEventListener("click", toggleTheme);

    navbarEnd.insertBefore(button, navbarEnd.firstChild);
    updateToggleLabel();
  }

  /**
   * Icon basename under img/vcs/*.svg (white artwork; CSS may filter in header / mast).
   */
  function vcsIconIdFromUrl(url) {
    if (!url) return "code";
    let host;
    try {
      host = new URL(url).hostname.toLowerCase();
    } catch {
      return "code";
    }
    if (host === "github.com" || host === "raw.githubusercontent.com" || host === "github.dev" || host.endsWith(".github.com")) {
      return "github";
    }
    if (host === "bitbucket.org" || host.includes("bitbucket.")) return "bitbucket";
    if (host.includes("gitlab")) return "gitlab";
    if (host === "codeberg.org" || host.endsWith(".codeberg.page") || host.endsWith(".codeberg.org")) {
      return "codeberg";
    }
    if (host.includes("gitea")) return "gitea";
    if (host.includes("forgejo")) return "forgejo";
    if (host.includes("sourcehut") || host.endsWith("sr.ht") || host === "git.sr.ht") {
      return "sourcehut";
    }
    if (host === "dev.azure.com" || host === "dev.azure" || host.endsWith("visualstudio.com") || host.includes("vssps.visualstudio.com")) {
      return "code";
    }
    return "code";
  }

  function vcsIconUrl(base, id) {
    const root = (base || ".").replace(/\/?$/, "/");
    return `${root}img/vcs/${id}.svg`;
  }

  function applyVcsIcons() {
    const base = getUiBase();
    function setVcsImage(img, href) {
      if (!img || !href) return;
      const id = vcsIconIdFromUrl(href);
      const primary = vcsIconUrl(base, id);
      img.onerror = function adtVcsOerr() {
        img.onerror = null;
        if (img.getAttribute("data-adt-vcs-tried") === "1") return;
        img.setAttribute("data-adt-vcs-tried", "1");
        if (!img.src || img.src.indexOf("code.svg") < 0) {
          img.src = vcsIconUrl(base, "code");
        }
      };
      img.src = primary;
    }
    document.querySelectorAll("a.adt-edit-inline-link[href]").forEach((a) => {
      const img = a.querySelector("img.adt-vcs-icon-img, img.adt-edit-vcs-img");
      setVcsImage(img, a.href);
    });
    document.querySelectorAll("a.adt-header-vcs[href] img.adt-header-vcs-img").forEach((img) => {
      const a = img.closest("a");
      if (a) setVcsImage(img, a.href);
    });
    document.querySelectorAll("a.vcs-repo-link[href] img.vcs-logo-img").forEach((img) => {
      const a = img.closest("a");
      if (a) setVcsImage(img, a.href);
    });
  }

  function getRepoUrl() {
    const meta = document.querySelector('meta[name="antora-repo-url"]');
    if (meta && meta.content) return meta.content;
    const editLink = document.querySelector(
      '.navbar-end a[href*="/edit/"], .navbar-end a[href*="/-/edit/"], .navbar-end a[href*="/blob/"], a.adt-edit-inline-link[href*="/"]'
    );
    if (editLink && editLink.href) {
      try {
        const u = new URL(editLink.href);
        const pathParts = u.pathname.split("/").filter(Boolean);
        if (u.hostname.includes("github") && pathParts.length >= 2) {
          return u.origin + "/" + pathParts.slice(0, 2).join("/");
        }
        if (u.hostname.includes("gitlab") && pathParts.length >= 2) {
          return u.origin + "/" + pathParts.slice(0, 2).join("/");
        }
        if (u.hostname.includes("bitbucket") && pathParts.length >= 2) {
          return u.origin + "/" + pathParts.slice(0, 2).join("/");
        }
        if (pathParts.length >= 2) return u.origin + "/" + pathParts.slice(0, 2).join("/");
      } catch {
        // ignore
      }
    }
    return null;
  }

  function getUiBase() {
    const fromData = document.querySelector("#site-script")?.dataset?.uiRootPath;
    if (fromData) return fromData;
    const script = document.currentScript;
    if (script?.src) {
      try {
        const u = new URL(script.src);
        u.pathname = u.pathname.replace(/\/[^/]*$/, "/");
        return u.pathname + u.search || ".";
      } catch (_e) {
        // ignore
      }
    }
    return ".";
  }

  function buildVcsLogoWidget(repoUrl, id, base) {
    const logoUrl = vcsIconUrl(base, id || "code");
    const wrapper = document.createElement("div");
    wrapper.className = "navbar-item vcs-repo-logo";
    const a = document.createElement("a");
    a.href = repoUrl || "#";
    a.className = "vcs-repo-link";
    a.setAttribute("aria-label", repoUrl ? "View repository" : "Repository");
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    const logo = document.createElement("div");
    logo.className = "vcs-logo";
    const img = document.createElement("img");
    img.alt = "";
    img.width = 24;
    img.height = 24;
    img.className = "vcs-logo-img";
    img.src = logoUrl;
    img.onerror = function () {
      this.onerror = null;
      const dataRoot = document.querySelector("#site-script")?.dataset?.uiRootPath;
      const root = (dataRoot || ".").replace(/\/?$/, "/");
      const tryCode = `${root}img/vcs/code.svg`;
      if (this.src && !this.src.includes("code.svg")) {
        this.src = tryCode;
        return;
      }
      this.src = `${root}img/vcs/repo.svg`;
    };
    logo.appendChild(img);
    a.appendChild(logo);
    wrapper.appendChild(a);
    return wrapper;
  }

  function replaceDownloadWithVcsLogo() {
    const downloadLink = document.querySelector(
      '.navbar .navbar-end a.button[href="#"], .navbar .navbar-end a.button.is-primary'
    );
    if (!downloadLink) return;
    const isDownload = /Download/i.test(downloadLink.textContent || "");
    if (!isDownload) return;
    const repoUrl = getRepoUrl();
    const iconId = repoUrl ? vcsIconIdFromUrl(repoUrl) : "code";
    const navbarEnd = document.querySelector(".navbar .navbar-end");
    if (!navbarEnd) return;
    const base = getUiBase();
    const widget = buildVcsLogoWidget(repoUrl, iconId, base);
    const toReplace = downloadLink.closest(".control") || downloadLink.closest(".navbar-item") || downloadLink;
    toReplace.parentNode.replaceChild(widget, toReplace);
  }

  function init() {
    applyInitialTheme();
    ensureToggleButton();
    replaceDownloadWithVcsLogo();
    applyVcsIcons();
  }

  if (document.readyState === "loading") {
    window.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
