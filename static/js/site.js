"use strict";

(() => {
  const menuToggle = document.querySelector(".menu-toggle");
  const menu = document.querySelector(".main-nav");
  const mobileQuery = window.matchMedia("(max-width: 760px)");

  const closeMenu = (returnFocus = false) => {
    if (!menuToggle || !menu) return;
    menuToggle.setAttribute("aria-expanded", "false");
    menu.classList.remove("is-open");
    document.body.classList.remove("menu-open");
    if (returnFocus) menuToggle.focus();
  };

  if (menuToggle && menu) {
    document.documentElement.classList.add("js-menu");
    menuToggle.addEventListener("click", () => {
      const opening = menuToggle.getAttribute("aria-expanded") !== "true";
      menuToggle.setAttribute("aria-expanded", String(opening));
      menu.classList.toggle("is-open", opening);
      document.body.classList.toggle("menu-open", opening);
    });

    menu.querySelectorAll('a[href^="#"]').forEach((link) => {
      link.addEventListener("click", () => {
        closeMenu();
        const target = document.getElementById(link.hash.slice(1));
        if (target && mobileQuery.matches) {
          // Move focus to the destination so keyboard users continue there.
          target.setAttribute("tabindex", "-1");
          target.focus({ preventScroll: true });
          target.addEventListener("blur", () => target.removeAttribute("tabindex"), { once: true });
        }
      });
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && menuToggle.getAttribute("aria-expanded") === "true") {
        closeMenu(true);
      }
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest(".site-header")) closeMenu();
    });

    document.addEventListener("focusin", (event) => {
      if (!event.target.closest(".site-header")) closeMenu();
    });

    mobileQuery.addEventListener("change", () => closeMenu());
  }

  const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
  const revealElements = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !motionQuery.matches) {
    const revealObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.06, rootMargin: "0px 0px 30px 0px" });

    document.documentElement.classList.add("js-motion");
    revealElements.forEach((element) => revealObserver.observe(element));
    motionQuery.addEventListener("change", (event) => {
      if (event.matches) {
        document.documentElement.classList.remove("js-motion");
        revealObserver.disconnect();
      }
    });
  }

  const sectionLinks = [...document.querySelectorAll('.main-nav a[href^="#"]')];
  if ("IntersectionObserver" in window && sectionLinks.length) {
    const visibleSections = new Set();
    const sectionObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) visibleSections.add(entry.target.id);
        else visibleSections.delete(entry.target.id);
      });
      const current = sectionLinks.find((link) => visibleSections.has(link.hash.slice(1)));
      sectionLinks.forEach((link) => {
        if (link === current) link.setAttribute("aria-current", "location");
        else link.removeAttribute("aria-current");
      });
    }, { rootMargin: "-15% 0px -50% 0px", threshold: 0 });
    sectionLinks.forEach((link) => {
      const section = document.getElementById(link.hash.slice(1));
      if (section) sectionObserver.observe(section);
    });
  }
})();
