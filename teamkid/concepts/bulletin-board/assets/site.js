/* TeamKid Williamston — Concept 1 "Bulletin Board". Small, dependency-free behaviours. */
(function () {
  "use strict";

  var root = document.documentElement;
  var THEME_KEY = "tk-theme-bulletin-board";
  var reduceMotion = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  root.classList.add("js");

  /* ---- theme (light = daytime classroom, dark = after hours) -------- */
  try {
    var saved = localStorage.getItem(THEME_KEY);
    if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);
  } catch (e) {}

  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-theme-toggle]");
    if (!t) return;
    var isDark = root.getAttribute("data-theme") === "dark" ||
      (!root.hasAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
    var next = isDark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem(THEME_KEY, next); } catch (err) {}
  });

  /* ---- sticky header ------------------------------------------------ */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-stuck", window.scrollY > 8); };
    onScroll();
    addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- mobile nav --------------------------------------------------- */
  var burger = document.querySelector("[data-burger]");
  var nav = document.querySelector("[data-nav]");
  if (burger && nav) {
    var close = function (focusBurger) {
      nav.classList.remove("is-open");
      burger.setAttribute("aria-expanded", "false");
      if (focusBurger) burger.focus();
    };
    burger.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      burger.setAttribute("aria-expanded", String(open));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) close(false);
    });
    addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) close(true);
    });
  }

  /* ---- die-cut paper letters ---------------------------------------- */
  // Seeded so the letters are "randomly" stapled up the same way every visit.
  function rng(seed) {
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  document.querySelectorAll("[data-cutout]").forEach(function (h) {
    var text = h.textContent.replace(/\s+/g, " ").trim();
    if (!text) return;
    var colours = (h.getAttribute("data-cutout") || "tomato grape marigold sky").split(/\s+/);
    var seed = 0;
    for (var i = 0; i < text.length; i++) seed = (seed * 31 + text.charCodeAt(i)) | 0;
    var rand = rng(seed);

    var sr = document.createElement("span");
    sr.className = "sr-only";
    sr.textContent = text;

    var vis = document.createElement("span");
    vis.setAttribute("aria-hidden", "true");
    var last = -1;
    text.split(" ").forEach(function (word, wi) {
      if (wi) vis.appendChild(document.createTextNode(" "));
      var w = document.createElement("span");
      w.className = "cw";
      Array.prototype.forEach.call(word, function (ch) {
        var l = document.createElement("span");
        var c;
        do { c = Math.floor(rand() * colours.length); } while (colours.length > 1 && c === last);
        last = c;
        l.className = "cl c-" + colours[c] + (rand() < .34 && /\w/.test(ch) ? " st" : "");
        l.style.setProperty("--r", ((rand() - .5) * 13).toFixed(1) + "deg");
        l.style.setProperty("--y", ((rand() - .5) * .09).toFixed(3) + "em");
        l.style.setProperty("--sr", ((rand() - .5) * 30).toFixed(0) + "deg");
        l.textContent = ch;
        w.appendChild(l);
      });
      vis.appendChild(w);
    });
    h.textContent = "";
    h.appendChild(sr);
    h.appendChild(vis);
  });

  /* ---- scroll reveal (cards settle onto the board; always visible) --- */
  var reveals = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || reduceMotion) {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var i = Number(el.getAttribute("data-delay") || 0);
        setTimeout(function () { el.classList.add("is-in"); }, i * 90);
        io.unobserve(el);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
    reveals.forEach(function (el) { io.observe(el); });
  }

  /* ---- role filters (paper tabs) ------------------------------------ */
  var filterBar = document.querySelector("[data-filters]");
  if (filterBar) {
    var roles = Array.prototype.slice.call(document.querySelectorAll("[data-tags]"));
    var count = document.querySelector("[data-role-count]");
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-filter]");
      if (!btn) return;
      filterBar.querySelectorAll("[data-filter]").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b === btn));
      });
      var key = btn.getAttribute("data-filter");
      var shown = 0;
      roles.forEach(function (card) {
        var match = key === "all" || card.getAttribute("data-tags").split(" ").indexOf(key) > -1;
        card.hidden = !match;
        if (match) shown++;
      });
      if (count) count.textContent = shown + " roles";
    });
  }

  /* ---- covenant tabs (divider tabs) --------------------------------- */
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll('[role="tab"]'));
    var select = function (tab, focus) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) panel.hidden = !on;
      });
      if (focus) tab.focus();
    };
    group.addEventListener("click", function (e) {
      var tab = e.target.closest('[role="tab"]');
      if (tab) select(tab, false);
    });
    group.addEventListener("keydown", function (e) {
      var i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      var next = -1;
      if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = tabs.length - 1;
      if (next < 0) return;
      e.preventDefault();
      select(tabs[next], true);
    });
  });

  /* ---- contact form (no backend: hand off to the mail client) -------- */
  var form = document.querySelector("[data-mail-form]");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (form.checkValidity && !form.checkValidity()) {
        if (form.reportValidity) form.reportValidity();
        return;
      }
      var d = new FormData(form);
      var name = (d.get("name") || "").toString().trim();
      var email = (d.get("email") || "").toString().trim();
      var message = (d.get("message") || "").toString().trim();
      var body = message + "\n\n— " + (name || "a visitor") + (email ? " (" + email + ")" : "");
      location.href = "mailto:teamkidwilliamston@gmail.com" +
        "?subject=" + encodeURIComponent("Hello from the TeamKid website") +
        "&body=" + encodeURIComponent(body);
      var note = form.querySelector("[data-form-note]");
      if (note) note.hidden = false;
    });
  }

  /* ---- footer year --------------------------------------------------- */
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });
})();
