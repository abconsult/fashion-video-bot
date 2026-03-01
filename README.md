# Fashion Video Bot

Автоматизированная система на базе Telegram-бота для создания коротких рекламных видео (рилсов) для бизнеса по продаже одежды. 
Бот берет фото товара с маркетплейса, удаляет фон, "надевает" одежду на виртуальную AI-модель, анимирует её в 15-секундное видео и накладывает текст.

**Архитектура:** Serverless (FastAPI)  
**Инфраструктура:** Vercel (Функции + Cron), Upstash Redis (Очередь задач)  
**AI Сервисы:** ProTalk (LLM), Fashn.ai (Try-on), Kling AI (Video), remove.bg (Фон), Cloudinary (Сборка)  

---

## 🛠 Запуск проекта локально (с помощью ngrok)

Для локального тестирования всего пайплайна (от приема ссылки до отправки готового видео) вам потребуется туннелировать запросы из Telegram на ваш компьютер.

### 1. Подготовка окружения
1. Склонируйте репозиторий и установите зависимости:
```bash
git clone https://github.com/abconsult/fashion-video-bot.git
cd fashion-video-bot
python -m venv venv
source venv/bin/activate  # Для Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Скопируйте шаблон переменных окружения:
```bash
cp .env.example .env
```
Заполните ВСЕ ключи в файле `.env` (TELEGRAM_TOKEN, UPSTASH_*, API ключи). Без них Pydantic выдаст ошибку валидации.

### 2. Запуск локального сервера (FastAPI)
Для локального запуска нам потребуется `uvicorn`:
```bash
pip install uvicorn
uvicorn api.webhook:app --port 8000 --reload
```
*Ваш сервер запустится на `http://localhost:8000`*

### 3. Проброс Webhook через ngrok
1. Установите и запустите ngrok (он выдаст вам публичный HTTPS-адрес):
```bash
ngrok http 8000
```
2. Скопируйте HTTPS-адрес из терминала (например, `https://1234-abcd.ngrok-free.app`).

3. Зарегистрируйте этот адрес в Telegram. Для этого откройте браузер и вставьте ссылку:
```
https://api.telegram.org/bot<ВАШ_TELEGRAM_TOKEN>/setWebhook?url=https://1234-abcd.ngrok-free.app/api/webhook
```
*(Вы должны увидеть `{"ok":true,"result":true,"description":"Webhook was set"}`)*

### 4. Тестирование пайплайна
1. Напишите боту `/start` и отправьте ссылку на товар (например, с Wildberries). Бот ответит и положит задачу в локальный Redis.
2. **Имитация Vercel Cron:** Так как локально у вас нет планировщика Vercel, вам нужно вручную "дёргать" крон, чтобы двигать задачу по этапам. Откройте второе окно терминала и выполните:
```bash
curl -X POST -H "Authorization: Bearer <ВАШ_CRON_SECRET>" http://localhost:8000/api/cron
```
Каждый вызов этой команды будет продвигать задачу на 1 шаг вперед (Скрапинг -> Удаление фона -> Промпт -> Примерка -> Видео -> Отправка). На этапах генерации (WAITING_TRYON, WAITING_VIDEO) повторяйте вызов раз в 10-20 секунд, пока статус не поменяется на SUCCESS.

---

## 🚀 Деплой на Vercel (Production)

Приложение полностью адаптировано под бессерверную архитектуру Vercel. 

### Шаг 1. Импорт проекта
1. Авторизуйтесь на [Vercel](https://vercel.com/) и нажмите **Add New -> Project**.
2. Подключите ваш GitHub аккаунт и выберите этот репозиторий.
3. В разделе **Environment Variables** добавьте абсолютно все переменные, которые есть в вашем `.env` файле.

### Шаг 2. Деплой
1. Нажмите **Deploy**.
2. Дождитесь успешной сборки. Vercel выдаст вам рабочий домен (например, `fashion-video-bot.vercel.app`).

### Шаг 3. Настройка Webhook и Cron
1. **Установите Webhook** для production:
   Откройте в браузере:
   `https://api.telegram.org/bot<ВАШ_TELEGRAM_TOKEN>/setWebhook?url=https://<ВАШ_VERCEL_ДОМЕН>/api/webhook`
2. **Проверьте Cron:**
   Перейдите в дашборд проекта Vercel -> вкладка **Settings** -> **Cron Jobs**. Там должна появиться запись `/api/cron` (согласно `vercel.json`). Запуск будет происходить 1 раз в минуту.

### Шаг 4. Установка секрета в Vercel
Обязательно добавьте секрет для Cron:
1. Сгенерируйте случайную строку.
2. Добавьте переменную `CRON_SECRET` в Environment Variables на Vercel.
3. Vercel автоматически будет подставлять `Authorization: Bearer ВАШ_СЕКРЕТ` при вызове cron-функции.
