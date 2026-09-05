document.addEventListener("DOMContentLoaded", () => {
    const setupPasswordToggles = () => {
        document.querySelectorAll('input[type="password"]').forEach((input) => {
            if (input.dataset.passwordToggleReady === "true") return;

            const parent = input.parentElement;
            if (!parent) return;

            input.dataset.passwordToggleReady = "true";
            parent.classList.add("has-password-toggle");

            const button = document.createElement("button");
            button.type = "button";
            button.className = "ym-password-toggle";
            button.setAttribute("aria-label", "Show password");
            button.setAttribute("title", "Show password");
            button.innerHTML = `
                <svg class="eye-open" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"></path>
                    <circle cx="12" cy="12" r="3"></circle>
                </svg>
                <svg class="eye-closed" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="m3 3 18 18"></path>
                    <path d="M10.6 10.6A2 2 0 0 0 12 14a2 2 0 0 0 1.4-.6"></path>
                    <path d="M9.9 5.2A9.7 9.7 0 0 1 12 5c6 0 9.5 7 9.5 7a16.4 16.4 0 0 1-2.1 2.8"></path>
                    <path d="M6.6 6.6C3.9 8.4 2.5 12 2.5 12s3.5 7 9.5 7a9.8 9.8 0 0 0 4.4-1"></path>
                </svg>
            `;

            button.addEventListener("click", () => {
                const isHidden = input.type === "password";
                input.type = isHidden ? "text" : "password";
                button.classList.toggle("is-visible", isHidden);
                button.setAttribute("aria-label", isHidden ? "Hide password" : "Show password");
                button.setAttribute("title", isHidden ? "Hide password" : "Show password");
                input.focus();
            });

            parent.appendChild(button);
        });
    };

    const setupScrollRail = () => {
        if (!document.querySelector(".ym-login-stage")) return;
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

    setupPasswordToggles();
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
