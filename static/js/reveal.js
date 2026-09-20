/* Apparition au défilement (voir static/css/components/reveal.css).
   Chargé sans defer dans <head> pour poser .reveal-ready avant le premier rendu : sans cela les
   éléments clignoteraient (visibles, puis masqués, puis révélés). Sans IntersectionObserver ou
   avec prefers-reduced-motion, on ne fait rien et tout reste visible. */
(function () {
  var root = document.documentElement;
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!("IntersectionObserver" in window) || reduced) return;

  root.classList.add("reveal-ready");

  document.addEventListener("DOMContentLoaded", function () {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.1 }
    );
    document.querySelectorAll("[data-reveal]").forEach(function (el) {
      observer.observe(el);
    });
  });
})();
