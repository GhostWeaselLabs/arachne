/* Meridian Runtime - Enhanced Documentation Interactions */

document.addEventListener("DOMContentLoaded", function () {
    // Initialize Mermaid.js for diagram rendering
    if (typeof mermaid !== "undefined") {
        mermaid.initialize({
            startOnLoad: true,
            theme: "default",
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: "linear",
                padding: 15,
                nodeSpacing: 30,
                rankSpacing: 40,
            },
            themeVariables: {
                primaryColor: "#0066cc",
                primaryTextColor: "#000",
                primaryBorderColor: "#0066cc",
                lineColor: "#666",
                secondaryColor: "#f0f8f0",
                tertiaryColor: "#fdf2f8",
                fontFamily:
                    "IBM Plex Sans, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif",
            },
            securityLevel: "loose",
        });
    }

    // Prevent scrolling on Material for MkDocs annotations
    document.addEventListener(
        "click",
        function (e) {
            if (
                e.target.classList.contains("annotate") ||
                e.target.closest(".annotate")
            ) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
        },
        true,
    );

    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener("click", function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute("href"));
            if (target) {
                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
            }
        });
    });

    // Enhanced card hover effects
    document.querySelectorAll(".grid.cards li").forEach((card) => {
        card.addEventListener("mouseenter", function () {
            this.style.transition =
                "transform 200ms ease, box-shadow 200ms ease";
            this.style.transform = "translateY(-4px) scale(1.02)";
        });

        card.addEventListener("mouseleave", function () {
            this.style.transform = "translateY(0) scale(1)";
        });
    });

    // Add keyboard shortcuts for navigation
    document.addEventListener("keydown", function (e) {
        // Ctrl/Cmd + K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === "k") {
            e.preventDefault();
            const searchInput = document.querySelector(".md-search__input");
            if (searchInput) {
                searchInput.focus();
            }
        }

        // ESC to close search
        if (e.key === "Escape") {
            const searchInput = document.querySelector(".md-search__input");
            if (searchInput && document.activeElement === searchInput) {
                searchInput.blur();
            }
        }
    });

    // Add loading state to external links
    document.querySelectorAll('a[href^="http"]').forEach((link) => {
        link.addEventListener("click", function () {
            this.style.opacity = "0.7";
            setTimeout(() => {
                this.style.opacity = "1";
            }, 1000);
        });
    });
});

/* Meridian Halo local init (robust) */
(function ensureHaloInit() {
    function tryInit() {
        // Wait until the Halo script exposes the API
        if (
            !window.MeridianHalo ||
            typeof window.MeridianHalo.init !== "function"
        ) {
            return setTimeout(tryInit, 100);
        }

        // Ensure a container exists for the Halo UI if required
        let container = document.getElementById("meridian-halo");
        if (!container) {
            container = document.createElement("div");
            container.id = "meridian-halo";
            // Default placement; adjust as needed
            container.style.position = "fixed";
            container.style.top = "16px";
            container.style.right = "16px";
            container.style.zIndex = "1000";
            document.body.appendChild(container);
        }

        try {
            // Initialize with minimal options; keep aligned with local working setup
            window.MeridianHalo.init({
                target: "#meridian-halo",
            });
            console.log("[halo] initialized (local copy)");
        } catch (e) {
            console.warn("[halo] init failed (local copy):", e);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", tryInit);
    } else {
        tryInit();
    }
})();
