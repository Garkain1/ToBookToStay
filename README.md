# ToBookToStay

**ToBookToStay** – это проект платформы для аренды жилья, построенная на Django с использованием базы данных MySQL. Этот проект настроен для работы в контейнерах через Docker и включает поддержку переменных окружения через `django-environ`. Также поддерживается развертывание на AWS с использованием RDS для базы данных и S3 для хранения медиафайлов.

## Структура проекта

- **core/** – основное приложение Django.
- **requirements.txt** – список зависимостей Python.
- **wait_for_db.sh** – скрипт для ожидания запуска базы данных перед миграциями.
- **.env.example** – пример файла переменных окружения для использования с `django-environ`.
- **.dockerignore** – список файлов и папок, которые не будут копироваться в Docker-контейнер.
- **Dockerfile** – описание Docker-образа для приложения.
- **docker-compose.yml** – настройка Docker Compose для запуска приложения и базы данных.
- **.gitattributes** – файл для управления атрибутами файлов в Git.
- **.gitignore** – список файлов и папок, которые не будут добавлены в Git-репозиторий.

## Требования

Перед началом работы убедитесь, что у вас установлены следующие программы:

- **Docker** (v26.1 и выше)
- **Docker Compose** (v2.27 и выше)
- **Python** (v3.11)

## Установка и запуск проекта

Проект **ToBookToStay** можно запустить двумя способами: с помощью Docker Compose или вручную, без Docker. Ниже приведены оба варианта.

### Вариант 1: Запуск через Docker Compose

Этот вариант предпочтителен для быстрого развертывания проекта с минимальной настройкой окружения.

#### 1. Клонирование репозитория

Клонируйте проект на вашу локальную машину:

```bash
git clone https://github.com/ваш-репозиторий/ToBookToStay.git
cd ToBookToStay
```

#### 2. Настройка переменных окружения

В корне проекта есть файл `.env.example`. Создайте файл `.env` на основе этого примера и заполните его нужными значениями:

```bash
cp .env.example .env
```

Пример содержимого `.env`:

```
SECRET_KEY=your_django_secret_key_here

DEBUG=True

DB_NAME=to_book_to_stay_db
DB_USER=db_user
DB_PASSWORD=db_password
DB_HOST=db
DB_PORT=3306

DB_ROOT_PASSWORD=your_secure_password_here

AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_REGION=your-aws-region

ALLOWED_HOSTS=127.0.0.1,localhost

MYSQL_PORT=3306
DJANGO_PORT=8000
```

#### 3. Запуск приложения через Docker

Запустите Docker и выполните команду для сборки и запуска проекта:

```bash
docker-compose up --build
```

Docker Compose автоматически соберет образ для вашего Django-приложения и запустит его вместе с контейнером базы данных MySQL. **Данные базы данных MySQL будут сохраняться в папке `./data`** в корневой директории проекта, что обеспечивает сохранение данных между перезапусками контейнеров.

#### 4. Скрипт для миграций

Скрипт `wait_for_db.sh` автоматически выполнит миграции после того, как база данных будет готова. Это происходит во время запуска контейнеров, поэтому **не нужно выполнять миграции вручную**.

#### 5. Создание суперпользователя

Для доступа к административной панели Django создайте суперпользователя:

```bash
docker-compose exec web python manage.py createsuperuser
```

Следуйте инструкциям, чтобы создать учетную запись суперпользователя.

#### 6. Доступ к приложению

После запуска контейнеров и выполнения миграций вы можете открыть браузер и перейти по адресу:

```
http://127.0.0.1:${DJANGO_PORT}
```

Порт по умолчанию указывается в файле `.env` через переменную `WEB_PORT`. Если вы изменили его в файле `.env`, используйте соответствующий порт:

```
http://127.0.0.1:<YOUR_CONFIGURED_PORT>
```

#### 7. Остановка проекта

Чтобы остановить проект, выполните:

```bash
docker-compose down
```

---

### Вариант 2: Запуск без Docker

Если вы хотите запустить проект локально без Docker, следуйте этим шагам:

#### 1. Клонирование репозитория

Клонируйте проект на вашу локальную машину:

```bash
git clone https://github.com/ваш-репозиторий/ToBookToStay.git
cd ToBookToStay
```

#### 2. Настройка виртуального окружения

Создайте виртуальное окружение и активируйте его:

```bash
python -m venv venv
source venv/bin/activate  # Для Linux/MacOS
# или
venv\Scripts\activate  # Для Windows
```

#### 3. Установка зависимостей

Установите зависимости из файла `requirements.txt`:

```bash
pip install -r requirements.txt
```

#### 4. Настройка переменных окружения

Скопируйте пример файла `.env` и настройте его:

```bash
cp .env.example .env
```

Отредактируйте файл `.env`, указав свои данные для базы данных и другие параметры.

#### 5. Настройка базы данных

Создайте базу данных в MySQL и настройте подключение в вашем файле `.env` (параметры `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).

Примените миграции для создания необходимых таблиц:

```bash
python manage.py migrate
```

#### 6. Запуск приложения

Запустите сервер разработки Django:

```bash
python manage.py runserver
```

Приложение будет доступно по адресу:

```
http://127.0.0.1:8000
```

#### 7. Создание суперпользователя

Создайте суперпользователя для доступа к админ-панели:

```bash
python manage.py createsuperuser
```

Следуйте инструкциям для создания суперпользователя.

#### 8. Остановка сервера

Для остановки сервера нажмите `Ctrl + C` в терминале, где запущен сервер разработки.

## Установка и запуск проекта на AWS

Проект **ToBookToStay** можно развернуть на AWS, используя Docker Compose. Это позволит вам быстро развернуть проект с минимальной настройкой окружения на EC2 экземпляре.

#### 1. Настройка EC2

Начните с развертывания EC2 экземпляра в AWS (например, Amazon Linux 2). На этом этапе вам нужно будет выполнить следующие шаги:

- **Настроить ключи доступа SSH** для подключения к вашему серверу.
- **Открыть порты** 22 (SSH), 80 (HTTP), 443 (HTTPS), и 8000 (для приложения Django) в Security Group для доступа извне.
- **(Опционально) Назначить IAM роль** вашему EC2 экземпляру для доступа к S3 и другим AWS сервисам без необходимости указания ключей доступа напрямую.

После настройки EC2, вы можете подключиться к вашему серверу по SSH и приступить к установке необходимых инструментов.

#### 2. Установка необходимых инструментов

Подключитесь к вашему EC2 экземпляру по SSH и выполните следующие команды для установки Git, Docker и Docker Compose:

```
# Обновление системы
sudo yum update -y

# Установка Git
sudo yum install git -y
git --version

# Установка Docker
sudo yum install docker -y
sudo systemctl start docker
sudo systemctl enable docker
docker --version

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

#### 3. Клонирование репозитория

Клонируйте репозиторий проекта на ваш EC2 сервер:

```bash
git clone https://github.com/ваш-репозиторий/ToBookToStay.git
cd ToBookToStay
```

#### 4. Настройка переменных окружения

В корне проекта есть файл `.env.example`. Создайте файл `.env` на основе этого примера и заполните его значениями, которые соответствуют вашему окружению:

```bash
cp .env.example .env
```

Пример содержимого `.env` для AWS:

```bash
SECRET_KEY=your_django_secret_key_here

DEBUG=True

DB_NAME=to_book_to_stay_db
DB_USER=db_user
DB_PASSWORD=db_password
DB_HOST=db
DB_PORT=3306

DB_ROOT_PASSWORD=your_secure_password_here

AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_REGION=your-aws-region

ALLOWED_HOSTS=127.0.0.1,localhost,your-ec2-public-ip

MYSQL_PORT=3306
DJANGO_PORT=8000
```

1. **AWS_ACCESS_KEY_ID** и **AWS_SECRET_ACCESS_KEY** — это ваши ключи доступа AWS (если вы не настроили IAM роль).
2. **AWS_STORAGE_BUCKET_NAME** — имя вашего S3 бакета для хранения медиафайлов.
3. **AWS_REGION** — регион вашего S3 бакета (например, `eu-central-1` для Франкфурта).
4. **ALLOWED_HOSTS** — обязательно добавьте публичный IP-адрес вашего EC2 экземпляра, чтобы разрешить доступ к приложению через этот IP.

#### 5. Запуск приложения через Docker Compose

После настройки переменных окружения, вы можете запустить проект с помощью Docker Compose. Это автоматически запустит как Django-приложение, так и базу данных MySQL.

```bash
docker-compose up --build -d
```

Docker Compose соберет образ для вашего Django-приложения и запустит его вместе с контейнером базы данных MySQL. Приложение будет доступно по адресу:

```
http://your-ec2-public-ip:8000
```

#### 6. Создание суперпользователя

Чтобы создать суперпользователя для доступа к административной панели Django, выполните команду:

```bash
docker-compose exec web python manage.py createsuperuser
```

Следуйте инструкциям, чтобы создать учетную запись суперпользователя.

#### 7. Остановка контейнеров

Если вам нужно остановить проект, выполните следующую команду:

```bash
docker-compose down
```

Эта команда остановит все контейнеры и удалит созданные ресурсы.

---

## Используемые технологии

- **Django** (v5.1.1) – фреймворк для веб-приложений.
- **MySQL** – реляционная база данных.
- **Docker** – контейнеризация приложения для упрощения развёртывания.
- **Docker Compose** – инструмент для управления многосервисными контейнерами.

---

## Авторы

Проект разработан **Sergei Oskolkov**

---

## Лицензия

Этот проект лицензирован под [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).

Вы можете:
- Делать копии, распространять и передавать этот проект.
- Изменять и адаптировать проект для своих нужд.

Условие:
- Вы должны указать авторство (Sergei Oskolkov, проект ToBookToStay) и предоставить ссылку на лицензию.
- Никакого коммерческого использования без разрешения.

Подробнее: [https://creativecommons.org/licenses/by-nc/4.0/](https://creativecommons.org/licenses/by-nc/4.0/)

---