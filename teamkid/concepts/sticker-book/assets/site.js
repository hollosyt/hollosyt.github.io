/* TeamKid Williamston · Sticker Book concept — small, dependency-free behaviours. */
(function () {
  "use strict";

  var root = document.documentElement;
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var canAnimate = "IntersectionObserver" in window && !reduce;
  // Gold stars start un-stuck only when we know we can stick them on again.
  if (canAnimate) root.classList.add("sb-motion");

  /* ---- theme -------------------------------------------------------- */
  try {
    var saved = localStorage.getItem("tk-theme");
    if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);
  } catch (e) {}

  document.addEventListener("click", function (e) {
    var t = e.target.closest("[data-theme-toggle]");
    if (!t) return;
    var isDark = root.getAttribute("data-theme") === "dark" ||
      (!root.hasAttribute("data-theme") && matchMedia("(prefers-color-scheme: dark)").matches);
    var next = isDark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("tk-theme", next); } catch (err) {}
  });

  /* ---- sticky header ------------------------------------------------ */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-stuck", header.getBoundingClientRect().top <= 0 && window.scrollY > 8); };
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

  /* ---- press-and-stick bounce --------------------------------------- */
  document.addEventListener("click", function (e) {
    if (reduce) return;
    var s = e.target.closest(".stk, .fact, .chip, .pill");
    // Big sheets (the form, the closing band) and form fields don't bounce.
    if (!s || s.matches(".form, .band") || e.target.closest("input, textarea, a")) return;
    s.classList.remove("is-pressed");
    void s.offsetWidth; // restart the animation
    s.classList.add("is-pressed");
  });
  document.addEventListener("animationend", function (e) {
    if (e.animationName === "sb-press") e.target.classList.remove("is-pressed");
    if (e.animationName === "sb-slap") e.target.classList.remove("is-in");
  });

  /* ---- reveal: visible at rest, a little slap-on as it scrolls in ---- */
  if (canAnimate) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        var delay = Number(el.dataset.delay || 0) * 90;
        setTimeout(function () { el.classList.add("is-in"); }, delay);
        io.unobserve(el);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.12 });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  }

  /* ---- reward chart: a gold star sticks onto each month ------------- */
  var cells = document.querySelectorAll("[data-chart] .cell");
  if (cells.length) {
    if (!canAnimate) {
      cells.forEach(function (c) { c.classList.add("is-in"); });
    } else {
      var starIO = new IntersectionObserver(function (entries) {
        var batch = entries.filter(function (en) { return en.isIntersecting; });
        batch.forEach(function (en, i) {
          setTimeout(function () { en.target.classList.add("is-in"); }, i * 170);
          starIO.unobserve(en.target);
        });
      }, { rootMargin: "0px 0px -10% 0px", threshold: 0.5 });
      cells.forEach(function (c) { starIO.observe(c); });
    }
  }

  /* ---- role filters ------------------------------------------------- */
  var filterBar = document.querySelector("[data-filters]");
  if (filterBar) {
    var roles = Array.prototype.slice.call(document.querySelectorAll("[data-tags]"));
    var count = document.querySelector("[data-role-count]");
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest(".filter");
      if (!btn) return;
      filterBar.querySelectorAll(".filter").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b === btn));
      });
      var key = btn.dataset.filter;
      var shown = 0;
      roles.forEach(function (card) {
        var match = key === "all" || card.dataset.tags.split(" ").indexOf(key) > -1;
        card.hidden = !match;
        if (match) shown++;
      });
      if (count) count.textContent = shown + " roles";
    });
  }

  /* ---- tabs (covenants) --------------------------------------------- */
  document.querySelectorAll("[data-tabs]").forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll('[role="tab"]'));
    var select = function (tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", String(on));
        t.tabIndex = on ? 0 : -1;
        var panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) panel.hidden = !on;
      });
    };
    group.addEventListener("click", function (e) {
      var tab = e.target.closest('[role="tab"]');
      if (tab) select(tab);
    });
    group.addEventListener("keydown", function (e) {
      var i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      var next = null;
      if (e.key === "ArrowRight" || e.key === "ArrowDown") next = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft" || e.key === "ArrowUp") next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = tabs.length - 1;
      if (next === null) return;
      e.preventDefault();
      tabs[next].focus();
      select(tabs[next]);
    });
  });

  /* ---- contact form (no backend: hand off to the mail client) -------- */
  var form = document.querySelector("[data-mail-form]");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = form.querySelector('[name="email"]');
      if (email && !email.checkValidity()) {
        email.reportValidity();
        return;
      }
      var d = new FormData(form);
      var name = (d.get("name") || "").toString().trim();
      var from = (d.get("email") || "").toString().trim();
      var message = (d.get("message") || "").toString().trim();
      var body = message + "\n\n— " + (name || "a visitor") + (from ? " (" + from + ")" : "");
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
