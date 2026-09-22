document.addEventListener("DOMContentLoaded", function () {

    const themeToggle = document.getElementById("theme-toggle");

    if (!themeToggle) return;

    const savedTheme = localStorage.getItem("chat-theme");

    function updateThemeIcon() {
        if (document.body.classList.contains("dark-theme")) {
            themeToggle.textContent = "☀";
            themeToggle.title = "فعال کردن حالت روشن";
        } else {
            themeToggle.textContent = "☾";
            themeToggle.title = "فعال کردن حالت تاریک";
        }
    }

    // تم ذخیره‌شده
    if (savedTheme === "dark") {
        document.body.classList.add("dark-theme");
    }

    updateThemeIcon();

    // تغییر تم
    themeToggle.addEventListener("click", function () {

        document.body.classList.toggle("dark-theme");

        const isDark =
            document.body.classList.contains("dark-theme");

        localStorage.setItem(
            "chat-theme",
            isDark ? "dark" : "light"
        );

        updateThemeIcon();
    });

});