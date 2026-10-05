/* TeamKid Bible Club · Sunbeams concept · small, dependency-free behaviours. */
(function () {
  "use strict";

  var root = document.documentElement;
  var still = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- sticky header ------------------------------------------------ */
  var header = document.querySelector(".site-header");

  /* ---- the afternoon moves on: beams tilt a little as you scroll ----- */
  var beams = Array.prototype.slice.call(document.querySelectorAll("[data-beam]"));
  var ticking = false;
  var update = function () {
    ticking = false;
    var y = window.scrollY || window.pageYOffset || 0;
    if (header) header.classList.toggle("is-stuck", y > 8);
    if (still || !beams.length) return;
    var max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    var p = Math.min(1, Math.max(0, y / max)).toFixed(3);
    for (var i = 0; i < beams.length; i++) beams[i].style.setProperty("--afternoon", p);
  };
  var onScroll = function () {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  };
  update();
  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll, { passive: true });

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
    addEventListener("resize", function () {
      if (window.innerWidth >= 960 && nav.classList.contains("is-open")) close(false);
    }, { passive: true });
  }

  /* ---- scroll reveal (content is visible unless this runs) ----------- */
  var reveals = document.querySelectorAll(".reveal");
  if (reveals.length && !still && "IntersectionObserver" in window) {
    root.classList.add("reveal-on");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        setTimeout(function () { el.classList.add("is-in"); }, Number(el.dataset.delay || 0) * 90);
        io.unobserve(el);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
    reveals.forEach(function (el) { io.observe(el); });
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
        if (match) { shown++; card.classList.add("is-in"); }
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
      var next = -1;
      if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = tabs.length - 1;
      if (next < 0) return;
      e.preventDefault();
      tabs[next].focus();
      select(tabs[next]);
    });
  });

  /* ---- contact form (no backend: hand off to the mail app) ----------- */
  var form = document.querySelector("[data-mail-form]");
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var email = form.querySelector('[name="email"]');
      if (email && !email.checkValidity()) { email.reportValidity(); return; }
      var d = new FormData(form);
      var name = String(d.get("name") || "").trim();
      var from = String(d.get("email") || "").trim();
      var message = String(d.get("message") || "").trim();
      var body = message + "\n\n— " + (name || "a visitor") + (from ? " (" + from + ")" : "");
      location.href = "mailto:teamkidwilliamston@gmail.com" +
        "?subject=" + encodeURIComponent("Hello from the TeamKid website") +
        "&body=" + encodeURIComponent(body);
      var note = form.querySelector("[data-form-note]");
      if (note) note.hidden = false;
    });
  }
})();
