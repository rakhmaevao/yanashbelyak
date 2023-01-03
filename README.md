# Проект сайта деревни Янашбеляк

## Подготовка к работе

```
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Прикрепи ссылку на файл БД gramps с именем `sqlite.db`.

## Как разрабатывать?

Запуск dev server, который пересобирается при изменении контента:

```
make devserver
```

Чтобы сгенерировать контент для локального dev server:
```
make local_content
```

## Как публиковать?
1. Убедись, что dev server не запущен.
2. Выполни команду:
```
make github
```