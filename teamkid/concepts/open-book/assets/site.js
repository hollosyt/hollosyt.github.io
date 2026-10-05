/* TeamKid Bible Club: Open Book. Small, dependency-free behaviours. */
(function () {
  "use strict";

  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- sticky header --------------------------------------------------- */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-stuck", window.scrollY > 8); };
    onScroll();
    addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- mobile menu ----------------------------------------------------- */
  var burger = document.querySelector("[data-burger]");
  var nav = document.querySelector("[data-nav]");
  if (burger && nav) {
    var setOpen = function (open, refocus) {
      nav.classList.toggle("is-open", open);
      burger.setAttribute("aria-expanded", String(open));
      if (!open && refocus) burger.focus();
    };
    burger.addEventListener("click", function () {
      setOpen(burger.getAttribute("aria-expanded") !== "true");
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });
    addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) setOpen(false, true);
    });
    document.addEventListener("click", function (e) {
      if (nav.classList.contains("is-open") && !nav.contains(e.target) && !burger.contains(e.target)) setOpen(false);
    });
    var desk = matchMedia("(min-width: 960px)");
    var onDesk = function () { if (desk.matches) setOpen(false); };
    if (desk.addEventListener) desk.addEventListener("change", onDesk);
  }

  /* ---- reveal on scroll ------------------------------------------------
     Only things below the fold are hidden, and only once JS is running, so
     everything is visible at rest and nothing above the fold ever blinks. */
  var reveals = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (!reduce && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.remove("is-pending");
        io.unobserve(entry.target);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });
    reveals.forEach(function (el) {
      if (el.getBoundingClientRect().top > innerHeight * 0.95) {
        el.classList.add("is-pending");
        io.observe(el);
      }
    });
  }

  /* ---- volunteer role filters ------------------------------------------ */
  var filterBar = document.querySelector("[data-filters]");
  if (filterBar) {
    var roles = Array.prototype.slice.call(document.querySelectorAll("[data-tags]"));
    var count = document.querySelector("[data-role-count]");
    filterBar.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-filter]");
      if (!btn) return;
      var key = btn.getAttribute("data-filter");
      filterBar.querySelectorAll("[data-filter]").forEach(function (b) {
        b.setAttribute("aria-pressed", String(b === btn));
      });
      var shown = 0;
      roles.forEach(function (card) {
        var match = key === "all" || card.getAttribute("data-tags").split(" ").indexOf(key) > -1;
        card.hidden = !match;
        if (match) shown++;
      });
      if (count) count.textContent = shown + " roles";
    });
  }

  /* ---- covenant tabs ---------------------------------------------------- */
  document.querySelectorAll("[data-tabs]").forEach(function (list) {
    var tabs = Array.prototype.slice.call(list.querySelectorAll('[role="tab"]'));
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
    list.addEventListener("click", function (e) {
      var tab = e.target.closest('[role="tab"]');
      if (tab) select(tab);
    });
    list.addEventListener("keydown", function (e) {
      var i = tabs.indexOf(document.activeElement);
      if (i < 0) return;
      var next = null;
      if (e.key === "ArrowRight") next = (i + 1) % tabs.length;
      else if (e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = tabs.length - 1;
      if (next === null) return;
      e.preventDefault();
      select(tabs[next], true);
    });
  });

  /* ---- contact form: no backend, hand off to the mail app --------------- */
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
