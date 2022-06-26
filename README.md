# Проект сайта деревни Янашбеляк

## Подготовка к работе

```
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Помести файл с БД в корень проекта, а в папку дерева помести ссылку на файл БД.

## Как разрабатывать?

Запуск pelican в режиме debug:

```
pelican --listen
```

Чтобы сгенерировать контент:
```
make content_wraper
```