(function () {
    const key = `yvm-scroll:${window.location.pathname}`;
    const maxAgeMs = 10 * 60 * 1000;

    function saveScrollPosition() {
        try {
            sessionStorage.setItem(key, JSON.stringify({
                x: window.scrollX || 0,
                y: window.scrollY || 0,
                at: Date.now()
            }));
        } catch (error) {
            // Session storage may be unavailable in private browsing modes.
        }
    }

    function restoreScrollPosition() {
        let saved = window.__YVM_SCROLL_RESTORE__ || null;
        try {
            saved = saved || JSON.parse(sessionStorage.getItem(key) || "null");
        } catch (error) {
            saved = null;
        }

        if (!saved || Date.now() - Number(saved.at || 0) > maxAgeMs) {
            document.documentElement.classList.remove("yvm-restoring-scroll");
            return;
        }

        const x = Number(saved.x || 0);
        const y = Number(saved.y || 0);
        const previousScrollBehavior = document.documentElement.style.scrollBehavior;
        const restore = () => {
            document.documentElement.style.scrollBehavior = "auto";
            window.scrollTo(x, y);
        };

        restore();
        requestAnimationFrame(() => {
            restore();
            setTimeout(() => {
                restore();
                document.documentElement.classList.remove("yvm-restoring-scroll");
                document.documentElement.style.scrollBehavior = previousScrollBehavior;
            }, 80);
        });

        setTimeout(() => {
            try {
                sessionStorage.removeItem(key);
            } catch (error) {
                // No-op.
            }
            window.__YVM_SCROLL_RESTORE__ = null;
        }, 180);
    }

    document.addEventListener("submit", saveScrollPosition, true);

    document.addEventListener("click", (event) => {
        const link = event.target.closest && event.target.closest("a[href]");
        if (!link || link.target === "_blank" || link.hasAttribute("download")) {
            return;
        }

        const href = link.getAttribute("href") || "";
        if (!href || href.startsWith("#") || href.startsWith("javascript:")) {
            return;
        }

        let url;
        try {
            url = new URL(href, window.location.href);
        } catch (error) {
            return;
        }

        if (url.origin === window.location.origin) {
            saveScrollPosition();
        }
    }, true);

    window.addEventListener("pageshow", restoreScrollPosition);
})();
