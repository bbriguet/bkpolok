/* « Display settings » : taille du texte, contraste élevé, mode sombre.
   Chargé sans defer dans <head> : les choix mémorisés s'appliquent à <html> avant le premier
   rendu (pas de flash). Les boutons (includes/display_settings.html) sont branchés une fois le
   DOM prêt ; sans JS, la barre reste masquée et le site suit les réglages du système.
   Les choix restent dans le stockage local du navigateur (voir la déclaration de confidentialité). */
(function () {
  var root = document.documentElement;
  var SIZES = ["100%", "112.5%", "125%", "150%", "175%"];

  function get(key) {
    try {
      return window.localStorage.getItem(key);
    } catch (error) {
      return null;
    }
  }

  function set(key, value) {
    try {
      window.localStorage.setItem(key, value);
    } catch (error) {
      /* stockage indisponible (navigation privée, réglages) : le choix vaut pour cette page */
    }
  }

  function matches(query) {
    return !!(window.matchMedia && window.matchMedia(query).matches);
  }

  var size = parseInt(get("bp-textsize") || "0", 10);
  if (!(size >= 0 && size < SIZES.length)) size = 0;
  var storedTheme = get("bp-theme");
  var contrast = get("bp-contrast") || (matches("(prefers-contrast: more)") ? "high" : "normal");

  function theme() {
    return storedTheme || (matches("(prefers-color-scheme: dark)") ? "dark" : "light");
  }

  root.setAttribute("data-textsize", String(size));
  root.setAttribute("data-theme", theme());
  root.setAttribute("data-contrast", contrast);

  document.addEventListener("DOMContentLoaded", function () {
    var bar = document.querySelector("[data-display-settings]");
    if (!bar) return;
    var toggle = bar.querySelector(".a11y-toggle");
    var panel = bar.querySelector(".a11y-panel");
    var status = bar.querySelector("[data-a11y-status]");
    var down = bar.querySelector('[data-text-size="down"]');
    var up = bar.querySelector('[data-text-size="up"]');
    var reset = bar.querySelector('[data-text-size="reset"]');
    var themeButton = bar.querySelector("[data-theme-toggle]");
    var contrastButton = bar.querySelector("[data-contrast-toggle]");

    /* Annonce aux lecteurs d'écran : vider puis remplir, pour qu'un message répété soit relu. */
    function say(text) {
      status.textContent = "";
      window.setTimeout(function () {
        status.textContent = text;
      }, 60);
    }

    function applySize(announce) {
      root.setAttribute("data-textsize", String(size));
      down.disabled = size === 0;
      up.disabled = size === SIZES.length - 1;
      set("bp-textsize", String(size));
      if (announce) say("Text size " + SIZES[size]);
    }

    function applyTheme(announce) {
      var current = theme();
      root.setAttribute("data-theme", current);
      themeButton.setAttribute("aria-pressed", current === "dark" ? "true" : "false");
      if (announce) say(current === "dark" ? "Dark mode on" : "Dark mode off");
    }

    function applyContrast(announce) {
      root.setAttribute("data-contrast", contrast);
      contrastButton.setAttribute("aria-pressed", contrast === "high" ? "true" : "false");
      if (announce) say(contrast === "high" ? "High contrast on" : "High contrast off");
    }

    down.addEventListener("click", function () {
      if (size > 0) {
        size -= 1;
        applySize(true);
      }
    });
    up.addEventListener("click", function () {
      if (size < SIZES.length - 1) {
        size += 1;
        applySize(true);
      }
    });
    reset.addEventListener("click", function () {
      size = 0;
      applySize(true);
    });
    themeButton.addEventListener("click", function () {
      storedTheme = theme() === "dark" ? "light" : "dark";
      set("bp-theme", storedTheme);
      applyTheme(true);
    });
    contrastButton.addEventListener("click", function () {
      contrast = contrast === "high" ? "normal" : "high";
      set("bp-contrast", contrast);
      applyContrast(true);
    });

    /* Sans choix explicite, le thème suit le système en direct. */
    if (window.matchMedia) {
      var query = window.matchMedia("(prefers-color-scheme: dark)");
      var follow = function () {
        if (!storedTheme) applyTheme(false);
      };
      if (query.addEventListener) query.addEventListener("change", follow);
      else if (query.addListener) query.addListener(follow);
    }

    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", open ? "false" : "true");
      panel.hidden = open;
      if (!open) {
        var first = panel.querySelector("button:not([disabled])");
        if (first) first.focus();
      }
    });

    applySize(false);
    applyTheme(false);
    applyContrast(false);
    bar.hidden = false;
  });
})();
