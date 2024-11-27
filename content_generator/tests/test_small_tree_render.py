import shutil
import sys

sys.path.append(".")

import os
from pathlib import Path

import pytest
from src.gramps_tree import GrampsTree
from src.small_tree_render import SmallTreeRender, WithoutRelationsError


@pytest.fixture(scope="session")
def _tmp_dir():
    os.makedirs("tmp", exist_ok=True)
    yield
    shutil.rmtree("tmp")


def test_normal_family(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0000", gramps_tree=tree, output_path=Path("tmp/test1.svg")
    )
    with Path("tmp/test1.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="400" height="300" viewBox="0 0 400 300">\n<defs>\n</defs>\n<path d="M150,25.0 L200,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M175.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,125.0 L200,125.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M175.0,125.0 L75.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M175.0,125.0 L275.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="pink" />\n<rect x="200" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<rect x="200" y="100" width="150" height="50" fill="pink" />\n<rect x="0" y="200" width="150" height="50" fill="pink" />\n<rect x="200" y="200" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0001.html" target="_parent">[...]><text x="25.499999999999993" y="25.0" font-size="12">Людмила Иванова</text>\n</a><a xlink:href="None/I0004.html" target="_parent">[...]><text x="215.6" y="25.0" font-size="12">Анатолий Навальный</text>\n</a><a xlink:href="None/I0000.html" target="_parent">[...]><text x="18.9" y="125.0" font-size="12">Алексей Навальный</text>\n</a><a xlink:href="None/I0003.html" target="_parent">[...]><text x="225.5" y="125.0" font-size="12">Юлия Абросимова</text>\n</a><a xlink:href="None/I0005.html" target="_parent">[...]><text x="25.499999999999993" y="225.0" font-size="12">Дарья Навальная</text>\n</a><a xlink:href="None/I0006.html" target="_parent">[...]><text x="225.5" y="225.0" font-size="12">Захар Навальный</text>\n</a></svg>'
        )


def test_without_relations(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    with pytest.raises(WithoutRelationsError):
        render.create_svg(
            base_person_id="I0013", gramps_tree=tree, output_path=Path("tmp/I0013.svg")
        )


def test_one_parent(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0004", gramps_tree=tree, output_path=Path("tmp/I0004.svg")
    )
    with Path("tmp/I0004.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="400" height="300" viewBox="0 0 400 300">\n<defs>\n</defs>\n<path d="M75.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,125.0 L200,125.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M175.0,125.0 L75.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M175.0,125.0 L275.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<rect x="200" y="100" width="150" height="50" fill="pink" />\n<rect x="0" y="200" width="150" height="50" fill="lightblue" />\n<rect x="200" y="200" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0014.html" target="_parent">[...]><text x="28.799999999999997" y="25.0" font-size="12">Иван Навальный</text>\n</a><a xlink:href="None/I0004.html" target="_parent">[...]><text x="15.599999999999994" y="125.0" font-size="12">Анатолий Навальный</text>\n</a><a xlink:href="None/I0001.html" target="_parent">[...]><text x="225.5" y="125.0" font-size="12">Людмила Иванова</text>\n</a><a xlink:href="None/I0000.html" target="_parent">[...]><text x="18.9" y="225.0" font-size="12">Алексей Навальный</text>\n</a><a xlink:href="None/I0002.html" target="_parent">[...]><text x="228.8" y="225.0" font-size="12">Олег Навальный</text>\n</a></svg>'
        )


def test_many_womans(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0007", gramps_tree=tree, output_path=Path("tmp/test2.svg")
    )
    with Path("tmp/test2.svg").open() as f:
        assert f.read() == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="1000" height="200" viewBox="0 0 1000 200">\n<defs>\n</defs>\n<path d="M150,37.5 L200,37.5" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M175.0,37.5 L112.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M175.0,37.5 L312.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,25.0 L400,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M375.0,25.0 L475.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,12.5 L600,12.5" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M575.0,12.5 L637.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M575.0,12.5 L837.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="lightblue" />\n<rect x="200" y="0" width="150" height="50" fill="pink" />\n<rect x="0" y="100" width="150" height="50" fill="pink" />\n<rect x="200" y="100" width="150" height="50" fill="pink" />\n<rect x="400" y="0" width="150" height="50" fill="pink" />\n<rect x="400" y="100" width="150" height="50" fill="pink" />\n<rect x="600" y="0" width="150" height="50" fill="pink" />\n<rect x="600" y="100" width="150" height="50" fill="lightblue" />\n<rect x="800" y="100" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0007.html" target="_parent">[...]><text x="28.799999999999997" y="25.0" font-size="12">Владимир Путин</text>\n</a><a xlink:href="None/I0008.html" target="_parent">[...]><text x="218.9" y="25.0" font-size="12">Людмила Шкребнева</text>\n</a><a xlink:href="None/I0009.html" target="_parent">[...]><text x="35.4" y="125.0" font-size="12">Мария Путина</text>\n</a><a xlink:href="None/I0010.html" target="_parent">[...]><text x="225.5" y="125.0" font-size="12">Катерина Путина</text>\n</a><a xlink:href="None/I0011.html" target="_parent">[...]><text x="412.3" y="25.0" font-size="12">Светлана Кривоногих</text>\n</a><a xlink:href="None/I0012.html" target="_parent">[...]><text x="442.0" y="125.0" font-size="12">Елизавета </text>\n</a><a xlink:href="None/I0015.html" target="_parent">[...]><text x="632.1" y="25.0" font-size="12">Алина Кабаева</text>\n</a><a xlink:href="None/I0016.html" target="_parent">[...]><text x="642.0" y="125.0" font-size="12">Иван Путин</text>\n</a><a xlink:href="None/I0017.html" target="_parent">[...]><text x="828.8" y="125.0" font-size="12">Владимир Путин</text>\n</a></svg>'
