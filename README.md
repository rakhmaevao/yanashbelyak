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

Чтобы сгенерировать контент:
```
make content
```

## Как публиковать?

Выполни команду:
```
make github
```