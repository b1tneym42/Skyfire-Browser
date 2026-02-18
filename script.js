const btn = document.getElementById('theme-btn');
const backToTopBtn = document.getElementById('backToTop');

// Темная тема
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-mode');
    if(btn) btn.textContent = '☀️';
}

if(btn) {
    btn.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        btn.textContent = isDark ? '☀️' : '🌓';
    });
}

// Кнопка Вверх
window.onscroll = function() {
    if (document.documentElement.scrollTop > 400) {
        if(backToTopBtn) backToTopBtn.classList.add('show');
    } else {
        if(backToTopBtn) backToTopBtn.classList.remove('show');
    }
};

function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function actionDownload() {
    alert("Сборка Skyfire Browser для Python доступна на GitHub. Перенаправляем в репозиторий.");
    window.open("https://github.com/b1tneym42/Skyfire-Browser", "_blank");
}