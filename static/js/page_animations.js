/* Yuvraj Medical - safe global micro animations */

document.addEventListener("DOMContentLoaded", () => {
    document.documentElement.classList.add("yvm-animate-ready");
    const body = document.body;

    const panel = document.getElementById("yvm-account-panel");
    const overlay = document.getElementById("yvm-side-overlay");
    const toggle = document.querySelector(".yvm-menu-toggle");

    if (panel && overlay && toggle) {
        panel.classList.remove("open");
        overlay.classList.remove("open");
        document.documentElement.classList.remove("yvm-menu-open");
        document.body.classList.remove("yvm-menu-open");
        document.body.style.top = "";
        panel.setAttribute("aria-hidden", "true");
        toggle.setAttribute("aria-expanded", "false");
    }

    document.querySelectorAll(".bg-particles").forEach((container) => {
        const allowParticles = body.classList.contains("yvm-page-login") || body.classList.contains("yvm-page-home");
        if (!allowParticles) {
            container.remove();
            return;
        }

        const existing = container.querySelectorAll("span").length;
        const needed = Math.max(0, 6 - existing);

        for (let index = 0; index < needed; index += 1) {
            container.appendChild(document.createElement("span"));
        }
    });

    const longRevealPage = (
        body.classList.contains("yvm-page-home") ||
        body.classList.contains("yvm-page-my-orders") ||
        body.classList.contains("yvm-page-rewards")
    );

    const revealItems = longRevealPage
        ? document.querySelectorAll(".card,.product-card,.order-card,.reward-card,.coupon-card,.history-card,.stat-card,.dashboard-card,.panel")
        : [];

    revealItems.forEach((item) => item.classList.add("yvm-reveal"));

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("yvm-is-visible");
                observer.unobserve(entry.target);
            });
        }, { threshold: 0.12 });

        revealItems.forEach((item) => observer.observe(item));
    } else {
        revealItems.forEach((item) => item.classList.add("yvm-is-visible"));
    }

    if (body.classList.contains("yvm-page-owner-dashboard")) {
        const counters = document.querySelectorAll(".value");
        const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        counters.forEach((counter) => {
            const original = counter.textContent.trim();
            const match = original.match(/-?\d+(?:,\d{3})*(?:\.\d+)?/);
            if (!match) return;

            const rawNumber = match[0];
            const target = Number(rawNumber.replace(/,/g, ""));
            if (!Number.isFinite(target)) return;

            const prefix = original.slice(0, match.index);
            const suffix = original.slice(match.index + rawNumber.length);
            const decimals = rawNumber.includes(".") ? rawNumber.split(".")[1].length : 0;

            if (reduceMotion) {
                counter.textContent = `${prefix}${target.toLocaleString(undefined, {
                    minimumFractionDigits: decimals,
                    maximumFractionDigits: decimals
                })}${suffix}`;
                return;
            }

            const start = performance.now();
            const duration = 900;

            function tick(now) {
                const progress = Math.min((now - start) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                const current = target * eased;
                counter.textContent = `${prefix}${current.toLocaleString(undefined, {
                    minimumFractionDigits: decimals,
                    maximumFractionDigits: decimals
                })}${suffix}`;

                if (progress < 1) {
                    requestAnimationFrame(tick);
                }
            }

            requestAnimationFrame(tick);
        });
    }

    document.querySelectorAll("button,.btn,a.action,a.primary,a.secondary,.login-btn,.mini-btn").forEach((button) => {
        if (button.dataset.yvmRippleReady === "true") return;
        button.dataset.yvmRippleReady = "true";

        button.addEventListener("click", function addRipple(event) {
            if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

            const ripple = document.createElement("span");
            const rect = this.getBoundingClientRect();

            ripple.className = "ripple";
            ripple.style.left = `${event.clientX - rect.left}px`;
            ripple.style.top = `${event.clientY - rect.top}px`;

            this.style.position = this.style.position || "relative";
            this.style.overflow = "hidden";
            this.appendChild(ripple);

            window.setTimeout(() => ripple.remove(), 600);
        });
    });
});
