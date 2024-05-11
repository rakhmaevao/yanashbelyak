# Проект сайта деревни Янашбеляк

## Подготовка к работе

```
poetry install --no-root
```

Прикрепи ссылку на файл БД gramps с именем `sqlite.db`.

```shell
ln -s /home/rakhmaevao/Documents/Genealogy/д.\ Янашбеляк/Дерево\ деревни/db/sqlite.db sqlite.db
```

## Как разрабатывать?

Запуск dev server, который пересобирается при изменении контента:

```
make devserver
```

Сервер будет доступен по адресу: http://127.0.0.1:8000.

Чтобы сгенерировать контент для локального dev server:

```
make local_content
```

При проблемах с локалью, помог [рецепт](https://stackoverflow.com/a/14548156/12993040). 

## Как публиковать?

1. Убедись, что dev server не запущен.
2. Выполни команду:

```
make github
```
