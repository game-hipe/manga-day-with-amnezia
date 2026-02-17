document.addEventListener('DOMContentLoaded', function() {
    const skuButtons = document.querySelectorAll('.sku-btn');
    const notification = document.getElementById('copyNotification');
    
    // Единая функция для визуального подтверждения успеха
    function handleSuccess(button) {
        // 1. Показываем всплывающее уведомление
        notification.textContent = 'Скопировано!';
        notification.style.backgroundColor = '#4CAF50';
        notification.classList.add('show');
        
        // Скрываем уведомление через 2 секунды
        setTimeout(() => {
            notification.classList.remove('show');
        }, 2000);
        
        // 2. Меняем стиль самой кнопки
        const originalText = button.textContent;
        const originalBg = button.style.backgroundColor;
        const originalColor = button.style.color;

        button.style.backgroundColor = '#4CAF50';
        button.style.color = 'white';
        button.textContent = 'Скопировано!';
        
        // Возвращаем кнопку в исходное состояние
        setTimeout(() => {
            button.style.backgroundColor = originalBg;
            button.style.color = originalColor;
            button.textContent = originalText === 'Скопировано!' ? 'Сюда' : originalText; 
            // Примечание: тут можно вернуть жестко 'Сюда' или старый текст, зависит от логики
        }, 2000);
    }

    // Функция обработки ошибок
    function handleError(err) {
        console.error('Ошибка копирования:', err);
        notification.textContent = 'Ошибка копирования';
        notification.style.backgroundColor = '#f44336'; // Красный цвет
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
            notification.style.backgroundColor = '#4CAF50'; // Возвращаем зеленый для будущих успехов
        }, 2000);
    }

    // Устаревший метод (Fallback) для HTTP или старых браузеров
    function fallbackCopy(text, button) {
        const textArea = document.createElement('textarea');
        
        // Стилизуем, чтобы элемент не был виден пользователю и не ломал верстку
        textArea.value = text;
        textArea.style.position = 'fixed'; // Избегаем прокрутки к низу страницы
        textArea.style.left = '-9999px';
        textArea.style.top = '0';
        
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                handleSuccess(button);
            } else {
                handleError('execCommand returned false');
            }
        } catch (err) {
            handleError(err);
        }
        
        document.body.removeChild(textArea);
    }

    // Основная логика клика
    skuButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const skuCode = this.getAttribute('data-sku');
            
            // Проверяем наличие API и контекст безопасности (HTTPS)
            if (navigator.clipboard && navigator.clipboard.writeText) {
                try {
                    await navigator.clipboard.writeText(skuCode);
                    handleSuccess(this);
                } catch (err) {
                    // Если Clipboard API есть, но выдал ошибку (например, permission denied)
                    // пробуем старый метод
                    fallbackCopy(skuCode, this);
                }
            } else {
                // Если API вообще нет (например, открыто через HTTP или file://)
                fallbackCopy(skuCode, this);
            }
        });
    });
});