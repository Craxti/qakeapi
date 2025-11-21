# Инструкция по публикации на PyPI

## Пакет готов к публикации

Пакет успешно собран:
- `dist/qakeapi-1.1.0-py3-none-any.whl`
- `dist/qakeapi-1.1.0.tar.gz`

## Шаги для публикации

### 1. Получите API токен на PyPI

1. Зайдите на https://pypi.org/manage/account/
2. Перейдите в раздел "API tokens"
3. Создайте новый токен с именем (например, "qakeapi-publish")
4. Скопируйте токен (он будет показан только один раз!)

### 2. Загрузите пакет на PyPI

**Вариант 1: Использовать токен напрямую**

```bash
py -m twine upload dist/*
```

При запросе:
- Username: `__token__`
- Password: вставьте ваш API токен (начинается с `pypi-`)

**Вариант 2: Использовать переменные окружения**

```bash
set TWINE_USERNAME=__token__
set TWINE_PASSWORD=pypi-ваш_токен_здесь
py -m twine upload dist/*
```

**Вариант 3: Использовать конфигурационный файл**

Создайте файл `~/.pypirc` (или `%USERPROFILE%\.pypirc` на Windows):

```ini
[pypi]
username = __token__
password = pypi-ваш_токен_здесь
```

Затем просто выполните:
```bash
py -m twine upload dist/*
```

## Проверка после публикации

После успешной публикации пакет будет доступен по адресу:
https://pypi.org/project/qakeapi/

Установка:
```bash
pip install qakeapi
```

## Примечания

- Убедитесь, что версия в `setup.py` и `pyproject.toml` соответствует версии в теге (v1.1.0)
- Если версия уже существует на PyPI, нужно увеличить версию
- После публикации изменения появятся на PyPI через несколько минут

