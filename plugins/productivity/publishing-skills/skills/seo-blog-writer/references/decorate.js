/*
 * decorate.js - client-side tooltip enabler for glossary auto-links.
 *
 * Drop this into your site <head> (or include it in your theme bundle) once,
 * and any <a class="glossary-term" data-definition="..."> link in your posts
 * gets a hover tooltip rendered from its data-definition attribute. The
 * inject-glossary-links.py script in scripts/ writes those attributes for
 * you; this script does the visual half.
 *
 * Defensive: if you hand-write a <a href="/glossary/<slug>/"> link without
 * running it through the injector, this script still tags it with the
 * glossary-term class and the target=_blank + rel=noopener attrs so the
 * styling and behavior stay consistent across the site.
 *
 * Skips the glossary index and individual term pages themselves (they have
 * their own definition styling).
 *
 * No dependencies. ~1 KB minified. Works in any browser that supports
 * querySelectorAll (IE9+).
 */
(function () {
  // The glossary pages themselves don't need tooltips on their own links.
  if (location.pathname.indexOf("/glossary/") === 0) return;

  // Inject the tooltip CSS once. Override by defining .glossary-term
  // styles in your own stylesheet AFTER this script runs.
  var style = document.createElement("style");
  style.textContent = [
    ".glossary-term {",
    "  border-bottom: 1px dotted currentColor;",
    "  text-decoration: none;",
    "  cursor: help;",
    "  position: relative;",
    "}",
    ".glossary-term:hover::after,",
    ".glossary-term:focus::after {",
    "  content: attr(data-definition);",
    "  position: absolute;",
    "  left: 0;",
    "  top: 100%;",
    "  margin-top: 0.25em;",
    "  z-index: 1000;",
    "  background: #111;",
    "  color: #fff;",
    "  padding: 0.5em 0.75em;",
    "  border-radius: 4px;",
    "  font-size: 0.85em;",
    "  font-weight: normal;",
    "  line-height: 1.4;",
    "  max-width: 320px;",
    "  width: max-content;",
    "  white-space: normal;",
    "  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);",
    "  pointer-events: none;",
    "}",
  ].join("\n");
  document.head.appendChild(style);

  function decorate() {
    var anchors = document.querySelectorAll('a[href*="/glossary/"]');
    for (var i = 0; i < anchors.length; i++) {
      var a = anchors[i];
      // If the injector already tagged it, we're done with this one.
      if (a.classList.contains("glossary-term")) continue;
      // Hand-written glossary link without injector attrs - apply the
      // baseline behavior. The tooltip won't render (no data-definition)
      // but at least the styling and open-in-new-tab are consistent.
      a.classList.add("glossary-term");
      a.setAttribute("target", "_blank");
      a.setAttribute("rel", "noopener");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", decorate);
  } else {
    decorate();
  }
})();
