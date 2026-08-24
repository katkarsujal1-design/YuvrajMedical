document.addEventListener("DOMContentLoaded", () => {
    const setupScrollRail = () => {
        if (document.getElementById("yvm-scroll-rail")) return;
        const rail = document.createElement("div");
        rail.id = "yvm-scroll-rail";
        rail.className = "yvm-scroll-rail";
        rail.setAttribute("aria-hidden", "true");
        rail.innerHTML = '<span class="yvm-scroll-thumb"></span>';
        document.body.appendChild(rail);
        const scroller = document.querySelector(".ym-login-panel") || document.documentElement;

        const update = () => {
            const maxScroll = Math.max(0, scroller.scrollHeight - scroller.clientHeight);
            const current = scroller === document.documentElement ? window.scrollY : scroller.scrollTop;
            const progress = maxScroll ? Math.min(1, Math.max(0, current / maxScroll)) : 0;
            rail.style.setProperty("--yvm-scroll-progress", progress.toFixed(4));
            rail.classList.toggle("is-visible", maxScroll > 24);
        };

        update();
        scroller.addEventListener("scroll", update, { passive: true });
        window.addEventListener("resize", update);
        window.setTimeout(update, 300);
    };

    setupScrollRail();

    const field = document.querySelector(".particle-field");

    if (field) {
        for (let i = 0; i < 55; i++) {
            const particle = document.createElement("span");
            particle.className = "particle";

            particle.style.left = Math.random() * 100 + "%";
            particle.style.top = Math.random() * 100 + "%";
            particle.style.setProperty("--x", (Math.random() * 80 - 40) + "px");
            particle.style.setProperty("--y", (Math.random() * -90 - 20) + "px");
            particle.style.setProperty("--duration", (6 + Math.random() * 8) + "s");
            particle.style.setProperty("--delay", (Math.random() * 5) + "s");

            field.appendChild(particle);
        }
    }

    setTimeout(() => {
        document.body.classList.add("intro-complete");
    }, 6200);
});
