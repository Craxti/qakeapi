// Простые интерактивные функции
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем анимацию появления для карточек
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
    });
    
    // Обработка форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="loading"></span> Отправка...';
                submitBtn.disabled = true;
            }
        });
    });
    
    console.log('🚀 QakeAPI Web App загружено!');
});