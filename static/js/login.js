document.addEventListener("DOMContentLoaded", () => {
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