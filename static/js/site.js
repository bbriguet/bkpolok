/* Comportements de page, chargés avec defer :
   - un lien vers un élément caché dans un « voir plus » (<details>) l'ouvre ;
   - avant l'impression, tous les « voir plus » s'ouvrent ;
   - le lien d'évitement donne vraiment le focus à <main> ;
   - les galeries protégées découragent l'enregistrement (menu contextuel, glisser-déposer). */
(function () {
  function openFor(hash) {
    if (!hash || hash.length < 2) return;
    var target;
    try {
      target = document.getElementById(decodeURIComponent(hash.slice(1)));
    } catch (error) {
      return;
    }
    var details = target && target.closest("details");
    while (details) {
      details.open = true;
      details = details.parentElement && details.parentElement.closest("details");
    }
  }

  window.addEventListener("hashchange", function () {
    openFor(window.location.hash);
  });
  document.addEventListener("click", function (event) {
    var link = event.target.closest && event.target.closest('a[href*="#"]');
    if (!link || link.pathname !== window.location.pathname) return;
    openFor(link.hash);
  });
  openFor(window.location.hash);

  window.addEventListener("beforeprint", function () {
    document.querySelectorAll("details").forEach(function (details) {
      details.open = true;
    });
  });

  var skip = document.querySelector(".skip-link");
  var main = document.getElementById("main");
  if (skip && main) {
    skip.addEventListener("click", function () {
      window.setTimeout(function () {
        main.focus();
      }, 0);
    });
  }

  document.querySelectorAll(".gallery--protected img").forEach(function (image) {
    image.addEventListener("contextmenu", function (event) {
      event.preventDefault();
    });
    image.addEventListener("dragstart", function (event) {
      event.preventDefault();
    });
  });
})();
