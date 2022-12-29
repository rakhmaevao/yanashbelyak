# Проект сайта деревни Янашбеляк

## Подготовка к работе

```
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Прикрепи ссылку на файл БД gramps с именем `sqlite.db`.

## Как разрабатывать?

Запуск pelican в режиме debug:

```
pelican --listen
```

Чтобы сгенерировать контент:
```
make content_wraper
```

## Как публиковать?

Выполни команду:
```
make github
```