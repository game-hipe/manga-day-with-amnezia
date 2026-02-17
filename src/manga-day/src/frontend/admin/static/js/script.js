"use strict";
const websocket = new WebSocket(`ws://${window.location.host}/admin/ws`);
var spiderStatus;
var alertLevel;
let activeMessages = [];
async function StartAllSpider() {
    try {
        await fetch("/admin/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                signal: "start",
                spider: "all"
            })
        });
    }
    catch (error) {
        console.error("Ошибка при отправке команды:", error);
    }
}
async function StopAllSpider() {
    const SpiderBox = document.getElementById("Spiders");
    if (!SpiderBox) {
        console.warn("Элемент 'Spiders' не найден.");
        return;
    }
    var stoppedSpider = 0;
    var spiders = SpiderBox.querySelectorAll(".spider p");
    for (let index = 0; index < spiders.length; index++) {
        const element = spiders[index];
        if (element.textContent === "not_running") {
            stoppedSpider++;
        }
    }
    if (stoppedSpider === spiders.length) {
        OnAlert("Все пауки уже остановлены!", "warning");
        return;
    }
    try {
        await fetch("/admin/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                signal: "stop",
                spider: "all"
            })
        });
    }
    catch (error) {
        console.error("Ошибка при отправке команды:", error);
    }
}
async function StartSpider(spiderName, page) {
    const SpiderBox = document.getElementById("Spiders");
    if (!SpiderBox) {
        console.warn("Элемент 'Spiders' не найден.");
        return;
    }
    var workSpider = 0;
    var spiders = SpiderBox.querySelectorAll(".spider p");
    for (let index = 0; index < spiders.length; index++) {
        const element = spiders[index];
        if (element.textContent != "not_running") {
            workSpider++;
        }
    }
    if (workSpider === spiders.length) {
        OnAlert("Все пауки уже остановлены!", "warning");
        return;
    }
    try {
        await fetch("/admin/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                signal: "start",
                spider: spiderName,
                page: page
            })
        });
    }
    catch (error) {
        console.error("Ошибка при отправке команды:", error);
    }
}
async function StopSpider(spiderName) {
    try {
        await fetch("/admin/command", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                signal: "stop",
                spider: spiderName
            })
        });
    }
    catch (error) {
        console.error("Ошибка при отправке команды:", error);
    }
}
function UpdateSpider(spider) {
    var _a;
    let spiderFound = false;
    const spiderBox = document.getElementById("Spiders");
    if (!spiderBox) {
        console.warn("Элемент 'Spiders' не найден.");
        return;
    }
    // Удаляем заглушку <strong>, если она есть
    const strong = spiderBox.querySelector("strong");
    strong === null || strong === void 0 ? void 0 : strong.remove();
    const spiderName = spider.name;
    const spiderStatus = spider.status;
    const spiderMessage = spider.message;
    const spiderChilds = spiderBox.querySelectorAll('.spider');
    // Поиск существующей карточки паука
    for (let index = 0; index < spiderChilds.length; index++) {
        const element = spiderChilds[index];
        const h1 = element.querySelector("h1");
        const p = element.querySelector("p");
        const b = element.querySelector("b");
        if (h1 && h1.innerText === spiderName) {
            spiderFound = true;
            // Создаём новую карточку взамен старой (чтобы не копить обработчики)
            if (p && p.innerText != spiderStatus || b && b.innerText != spiderMessage) {
                const newDiv = document.createElement("div");
                newDiv.className = "spider";
                // Заголовок с именем паука
                const newH1 = document.createElement("h1");
                newH1.textContent = spiderName;
                newDiv.appendChild(newH1);
                // Статус
                const newP = document.createElement("p");
                newP.textContent = spiderStatus;
                newDiv.appendChild(newP);
                newP.style.color = getColor(spiderStatus);
                // Сообщение
                const newB = document.createElement("b");
                newB.textContent = spiderMessage;
                newDiv.appendChild(newB);
                // Поле для номера страницы (может быть полезно)
                if (spiderStatus === "not_running") {
                    const pageInput = document.createElement("input");
                    // pageInput.setAttribute("type", "number");
                    newDiv.appendChild(pageInput);
                }
                // Кнопка с data-атрибутом (без обработчика)
                const newButton = document.createElement("button");
                newButton.textContent = spiderStatus === "not_running" ? "Начать парсинг" : "Остановить парсинг";
                newButton.dataset.spider = spiderName;
                newDiv.appendChild(newButton);
                // Заменяем старую карточку новой
                (_a = element.parentNode) === null || _a === void 0 ? void 0 : _a.replaceChild(newDiv, element);
                break;
            }
        }
    }
    // Если паук не найден, создаём новую карточку
    if (!spiderFound) {
        const divSpider = document.createElement("div");
        divSpider.className = "spider";
        const h1 = document.createElement("h1");
        h1.textContent = spiderName;
        divSpider.appendChild(h1);
        const p = document.createElement("p");
        p.style.color = getColor(spiderStatus);
        p.textContent = spiderStatus;
        divSpider.appendChild(p);
        const b = document.createElement("b");
        b.textContent = spiderMessage;
        divSpider.appendChild(b);
        if (spiderStatus === "not_running") {
            const pageInput = document.createElement("input");
            // pageInput.setAttribute("type", "number");
            divSpider.appendChild(pageInput);
        }
        const button = document.createElement("button");
        button.textContent = spiderStatus === "not_running" ? "Начать парсинг" : "Остановить парсинг";
        button.dataset.spider = spiderName; // сохраняем имя паука
        divSpider.appendChild(button);
        spiderBox.appendChild(divSpider);
    }
}
function getColor(status) {
    switch (status) {
        case "error":
            return "#F44336"; // Яркий красный - опасность, ошибка
        case "cancelled":
            return "#FF9800"; // Оранжевый - отмена, предупреждение
        case "not_running":
            return "#9E9E9E"; // Серый - неактивно, ожидание
        case "success":
            return "#4CAF50"; // Зеленый - успех, готово
        case "running":
            return "#2196F3"; // Синий - в процессе, активно
        case "processing":
            return "#FFC107"; // Янтарный - обработка, внимание
        default:
            return "";
    }
}
function OnAlert(message, level) {
    const messagesContainer = document.querySelector('.messages');
    if (!messagesContainer) {
        console.error('Контейнер для сообщений не найден!');
        return;
    }
    const messageId = 'msg_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const messageElement = document.createElement('div');
    messageElement.id = messageId;
    messageElement.className = `message ${level}`;
    messageElement.innerHTML = `<h1><span>${message}</span></h1>`;
    messagesContainer.appendChild(messageElement);
    activeMessages.push({
        id: messageId,
        element: messageElement
    });
    setTimeout(() => {
        const msgIndex = activeMessages.findIndex(msg => msg.id === messageId);
        if (msgIndex !== -1) {
            if (activeMessages[msgIndex].element && activeMessages[msgIndex].element.parentNode) {
                activeMessages[msgIndex].element.remove();
            }
            activeMessages.splice(msgIndex, 1);
        }
    }, 4000);
}
// --- Обработчик кликов через делегирование ---
document.addEventListener("DOMContentLoaded", () => {
    const spiderBox = document.getElementById("Spiders");
    if (spiderBox) {
        spiderBox.addEventListener("click", (event) => {
            var _a;
            const target = event.target;
            const button = target.closest("button");
            if (!button)
                return; // клик не по кнопке
            const spiderDiv = button.closest(".spider");
            if (!spiderDiv)
                return; // кнопка не внутри карточки паука
            const spiderName = button.dataset.spider;
            const spiderInput = spiderDiv.querySelector("input");
            var intPage = null;
            var stringPage = spiderInput === null || spiderInput === void 0 ? void 0 : spiderInput.value.trim();
            if (stringPage !== "" && stringPage !== undefined) {
                intPage = parseInt(stringPage);
                if (isNaN(intPage) || intPage <= 0) {
                    OnAlert("Число должно быть положительным целым числом!", "warning");
                    if (spiderInput) {
                        spiderInput.value = "";
                    }
                    return;
                }
            }
            if (!spiderName)
                return; // нет data-атрибута
            // Определяем действие по тексту кнопки
            if ((_a = button.textContent) === null || _a === void 0 ? void 0 : _a.includes("Начать")) {
                StartSpider(spiderName, intPage);
            }
            else {
                StopSpider(spiderName);
            }
        });
    }
});
document.addEventListener("DOMContentLoaded", () => {
    const spiderBox = document.getElementById("Spiders");
    if (spiderBox && !spiderBox.hasAttribute('data-listener-enter')) {
        spiderBox.setAttribute('data-listener-enter', 'true');
        spiderBox.addEventListener("keydown", (event) => {
            if (event.key !== "Enter")
                return;
            const target = event.target;
            if (!(target instanceof HTMLInputElement))
                return;
            const spiderDiv = target.closest(".spider");
            if (!spiderDiv)
                return;
            // Кнопка «Начать» в этой карточке
            const startButton = Array.from(spiderDiv.querySelectorAll('button'))
                .find(btn => { var _a; return (_a = btn.textContent) === null || _a === void 0 ? void 0 : _a.includes('Начать'); });
            if (!startButton)
                return;
            const spiderName = startButton.dataset.spider;
            if (!spiderName)
                return;
            const spiderInput = target;
            let intPage = null;
            const stringPage = spiderInput.value.trim();
            if (stringPage !== "") {
                intPage = parseInt(stringPage);
                if (isNaN(intPage) || intPage <= 0) {
                    OnAlert("Число должно быть положительным целым числом!", "warning");
                    spiderInput.value = "";
                    return;
                }
                // Если число корректное, intPage > 0, продолжаем
            } // иначе intPage остаётся null (без ограничения страниц)
            event.preventDefault(); // важно для input, чтобы не было лишних действий
            StartSpider(spiderName, intPage);
        });
    }
});
websocket.onmessage = function (event) {
    let answer = JSON.parse(event.data);
    if (answer.signal === "alert") {
        let result = answer.result;
        OnAlert(result.message, result.level);
    }
    else if (answer.signal === "status") {
        let result = answer.result;
        for (const element of result) {
            UpdateSpider(element);
        }
    }
};
websocket.onclose = () => {
    OnAlert("Соединение с сервером разорвано!", "critical");
};
