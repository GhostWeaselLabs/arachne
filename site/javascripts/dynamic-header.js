/**
 * Inject a small Meridian Halo next to the site title after the header renders,
 * replacing the default Material "book" glyph while keeping layout stable.
 *
 * Behavior:
 * - Locates the inline icon (SVG) before the site title and hides it (visibility: hidden).
 * - Inserts a span.mr-halo-wrap before that icon so the Halo visually replaces it.
 * - Falls back to inserting as the first child of the title container if no icon is found.
 * - Initializes a Meridian Halo instance using the standalone CDN bundle.
 * - Respects reduced motion preferences and dims brightness when page is hidden.
 * - Keeps particle count modest for performance.
 *
 * Assumptions:
 * - The Meridian Halo standalone bundle is included site-wide (via mkdocs.yml extra_javascript):
 *   https://unpkg.com/meridian-halo@latest/dist/meridian-halo.standalone.min.js
 *
 * Safe to include multiple times; the script checks for existing mounts.
 */

(function () {
    var HALO_ID = "mr-halo-icon";
    var HALO_SIZE = 28;
    var HIDE_ICON_CLASS = "mr-hide-title-icon";

    function log() {
        try {
            // Prefix logs for easy filtering
            var args = Array.prototype.slice.call(arguments);
            args.unshift("[halo]");
            console.log.apply(console, args);
        } catch {}
    }

    function warn() {
        try {
            var args = Array.prototype.slice.call(arguments);
            args.unshift("[halo]");
            console.warn.apply(console, args);
        } catch {}
    }

    function domReady(cb) {
        if (
            document.readyState === "complete" ||
            document.readyState === "interactive"
        ) {
            cb();
        } else {
            document.addEventListener("DOMContentLoaded", cb, { once: true });
        }
    }

    function hasHaloBundle() {
        var ok =
            typeof window !== "undefined" &&
            window.MeridianHalo &&
            typeof window.MeridianHalo.createHalo === "function";
        log("bundle", ok ? "ready" : "not ready");
        return ok;
    }

    function prefersReducedMotion() {
        try {
            var prm =
                window.matchMedia &&
                window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            log("prefersReducedMotion", prm);
            return prm;
        } catch (e) {
            return false;
        }
    }

    function ensureStyles() {
        // Inject minimal CSS once
        var styleId = "mr-halo-style";
        if (document.getElementById(styleId)) return;

        var css =
            "" +
            ".md-header .md-header__title{display:flex;align-items:center;gap:10px}" +
            /* Hide the original book glyph but keep its space to avoid layout jump */
            ".md-header .md-header__title ." +
            HIDE_ICON_CLASS +
            "{visibility:hidden}" +
            ".mr-halo-wrap{display:inline-flex;align-items:center;justify-content:center;position:relative;z-index:2147483647;pointer-events:none;" +
            "width:" +
            HALO_SIZE +
            "px;height:" +
            HALO_SIZE +
            "px;" +
            "min-width:" +
            HALO_SIZE +
            "px;min-height:" +
            HALO_SIZE +
            "px;" +
            "border-radius:50%;overflow:hidden;margin-left:0}" /* no extra margin; we occupy icon slot */ +
            ".mr-halo-wrap canvas{display:block;width:100%!important;height:100%!important}" +
            "@media(max-width:720px){.md-header .md-header__title{gap:8px}}" +
            "@media(prefers-reduced-motion: reduce){.mr-halo-wrap{display:none!important}}";

        var style = document.createElement("style");
        style.id = styleId;
        style.type = "text/css";
        style.appendChild(document.createTextNode(css));
        document.head.appendChild(style);
        log("styles injected");
    }

    function findTitleContainer() {
        // Try multiple selectors to be robust across theme versions
        var selectors = [
            ".md-header .md-header__title",
            ".md-header__title",
            ".md-header .md-header__ellipsis",
            ".md-header",
        ];
        for (var i = 0; i < selectors.length; i++) {
            var sel = selectors[i];
            var el = document.querySelector(sel);
            if (el) {
                log("container found via", sel);
                return el;
            }
            log("container not found via", sel);
        }
        warn("no suitable title container found");
        return null;
    }

    function createMountIfMissing(container) {
        var existing = document.getElementById(HALO_ID);
        if (existing) {
            log("mount exists");
            return existing;
        }

        var mount = document.createElement("span");
        mount.id = HALO_ID;
        mount.className = "mr-halo-wrap";
        mount.setAttribute("aria-hidden", "true");
        mount.setAttribute("title", "Meridian Halo");
        // Ensure stacking and stacking context without relying solely on CSS (inline fallback)
        mount.style.position = "relative";
        mount.style.zIndex = "2147483647";
        mount.style.pointerEvents = "none";

        // Preferred: insert before the title icon if present, otherwise prepend
        var icon = findTitleIcon(container);
        if (icon) {
            icon.classList.add(HIDE_ICON_CLASS);
            container.insertBefore(mount, icon);
            log("icon found and hidden; halo inserted before icon");
        } else {
            container.insertBefore(mount, container.firstChild);
            log("no icon found; halo inserted as first child");
        }
        return mount;
    }

    function initHalo(mount) {
        if (!hasHaloBundle()) {
            warn("bundle not ready at init");
            return;
        }

        // Avoid double-initialization (look for a canvas)
        if (mount.querySelector("canvas")) {
            log("canvas already present, skipping init");
            return;
        }

        try {
            // Header preset tuned for small size visibility + livelier motion
            var halo = window.MeridianHalo.createHalo({
                mount: mount,
                width: HALO_SIZE,
                height: HALO_SIZE,
                mode: "always-bright",
                styleCycle: { enabled: false },
                // Denser and slightly larger points for readability at 28px
                count: 2000,
                radius: HALO_SIZE * 0.48,
                pointSize: Math.max(2.5, HALO_SIZE * 0.057),
                // Motion tuning
                initialSpeed: 10.0,
                physics: {
                    gravityStrength: 100.0,
                    tangentialStrength: 100.0,
                    springK: 0.15,
                    damping: 0.05,
                    maxVel: 10.0,
                },
            });
            if (!halo) {
                warn("createHalo returned falsy");
                return;
            }
            // Subtle overall brightness boost
            if (typeof halo.setBrightness === "function") {
                halo.setBrightness(2.25);
            }
            log("init ok");

            // Pause/dim when tab not visible to save resources
            var hiddenKey = "hidden";
            var visibilityChange = "visibilitychange";
            if (typeof document.msHidden !== "undefined") {
                hiddenKey = "msHidden";
                visibilityChange = "msvisibilitychange";
            }
            if (typeof document.webkitHidden !== "undefined") {
                hiddenKey = "webkitHidden";
                visibilityChange = "webkitvisibilitychange";
            }

            function handleVisibility() {
                try {
                    var isHidden = document[hiddenKey];
                    if (typeof halo.setBrightness === "function") {
                        // Dim when hidden to save resources; keep boosted when visible
                        halo.setBrightness(isHidden ? 0.3 : 1.25);
                    }
                } catch {}
            }

            document.addEventListener(visibilityChange, handleVisibility);
            handleVisibility();

            // Cleanup on unload
            window.addEventListener("beforeunload", function () {
                try {
                    if (halo && typeof halo.destroy === "function")
                        halo.destroy();
                } catch {}
            });
        } catch (e) {
            warn("init error", e && e.message ? e.message : e);
        }
    }

    function mountOnce() {
        if (prefersReducedMotion()) return; // Respect user preference

        var container = findTitleContainer();
        if (!container) return;

        ensureStyles();
        var mount = createMountIfMissing(container);

        if (hasHaloBundle()) {
            initHalo(mount);
        } else {
            // Retry briefly if CDN script loads after DOM ready
            var retries = 0;
            var t = setInterval(function () {
                retries += 1;
                log("retry", retries);
                if (hasHaloBundle()) {
                    clearInterval(t);
                    initHalo(mount);
                } else if (retries > 30) {
                    clearInterval(t);
                    warn("bundle not available after retries");
                }
            }, 150);
        }
    }

    domReady(function () {
        log("ready");

        // Hide the left-side md-logo element so the Halo fully replaces it
        try {
            var header = document.querySelector(".md-header__inner");
            if (header && header.children && header.children.length > 0) {
                var firstChild = header.children[0];
                if (
                    firstChild &&
                    firstChild.matches &&
                    firstChild.matches("a.md-header__button.md-logo")
                ) {
                    // Force removal to avoid reflow re-insertion by theme scripts
                    firstChild.style.setProperty(
                        "display",
                        "none",
                        "important",
                    );
                    if (typeof firstChild.remove === "function") {
                        firstChild.remove();
                    } else if (firstChild.parentNode) {
                        firstChild.parentNode.removeChild(firstChild);
                    }
                    log("left md-logo removed");
                }
            }
        } catch (e) {
            warn(
                "failed to remove left md-logo",
                e && e.message ? e.message : e,
            );
        }

        mountOnce();

        // Header is initialized once; avoid remounting on client-side navigation events
        // to prevent duplicate work and visual jitter.
    });
    /**
     * Try to find the title icon element inside the header title.
     * Different theme versions may render the glyph differently.
     */
    function findTitleIcon(container) {
        // Common patterns:
        // 1) Inline SVG before the text
        var svg = container.querySelector("svg");
        if (svg) return svg;
        // 2) Any material icon element inside title
        var icon = container.querySelector(".md-icon");
        if (icon) return icon;
        // 3) No icon found
        return null;
    }
})();
