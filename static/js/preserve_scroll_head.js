(function () {
    const key = `yvm-scroll:${window.location.pathname}`;
    const maxAgeMs = 10 * 60 * 1000;

    try {
        const saved = JSON.parse(sessionStorage.getItem(key) || "null");
        if (!saved || Date.now() - Number(saved.at || 0) > maxAgeMs) {
            return;
        }

        if ("scrollRestoration" in history) {
            history.scrollRestoration = "manual";
        }

        window.__YVM_SCROLL_RESTORE__ = saved;
        document.documentElement.classList.add("yvm-restoring-scroll");

        const style = document.createElement("style");
        style.textContent = "html.yvm-restoring-scroll body{opacity:0!important;}";
        document.head.appendChild(style);
    } catch (error) {
        document.documentElement.classList.remove("yvm-restoring-scroll");
    }
})();
