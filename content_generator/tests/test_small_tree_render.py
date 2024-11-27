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
    # shutil.rmtree("tmp")


def test_normal_family(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0000", gramps_tree=tree, output_path=Path("tmp/test1.svg")
    )
    with Path("tmp/test1.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="340" height="300" viewBox="0 0 340 300">\n<defs>\n</defs>\n<path d="M150,25.0 L170,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,125.0 L170,125.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,125.0 L75.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M160.0,125.0 L245.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="pink" />\n<rect x="170" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<rect x="170" y="100" width="150" height="50" fill="pink" />\n<rect x="0" y="200" width="150" height="50" fill="pink" />\n<rect x="170" y="200" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0001.html" target="_parent">[...]><text x="25.499999999999993" y="25.0" font-size="12">Людмила Иванова</text>\n</a><a xlink:href="None/I0004.html" target="_parent">[...]><text x="185.6" y="25.0" font-size="12">Анатолий Навальный</text>\n</a><a xlink:href="None/I0000.html" target="_parent">[...]><text x="18.9" y="125.0" font-size="12">Алексей Навальный</text>\n</a><a xlink:href="None/I0003.html" target="_parent">[...]><text x="195.5" y="125.0" font-size="12">Юлия Абросимова</text>\n</a><a xlink:href="None/I0005.html" target="_parent">[...]><text x="25.499999999999993" y="225.0" font-size="12">Дарья Навальная</text>\n</a><a xlink:href="None/I0006.html" target="_parent">[...]><text x="195.5" y="225.0" font-size="12">Захар Навальный</text>\n</a></svg>'
        )


def test_without_relations(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    with pytest.raises(WithoutRelationsError):
        render.create_svg(
            base_person_id="I0013", gramps_tree=tree, output_path=Path("tmp/I0013.svg")
        )


def test_without_children(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0006", gramps_tree=tree, output_path=Path("tmp/I0006.svg")
    )
    with Path("tmp/I0006.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="340" height="200" viewBox="0 0 340 200">\n<defs>\n</defs>\n<path d="M150,25.0 L170,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="pink" />\n<rect x="170" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0003.html" target="_parent">[...]><text x="25.499999999999993" y="25.0" font-size="12">Юлия Абросимова</text>\n</a><a xlink:href="None/I0000.html" target="_parent">[...]><text x="188.9" y="25.0" font-size="12">Алексей Навальный</text>\n</a><a xlink:href="None/I0006.html" target="_parent">[...]><text x="25.499999999999993" y="125.0" font-size="12">Захар Навальный</text>\n</a></svg>'
        )

def test_only_parents(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0000", gramps_tree=tree, output_path=Path("tmp/I0000.svg")
    )


def test_many_womans(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0007", gramps_tree=tree, output_path=Path("tmp/test2.svg")
    )
    with Path("tmp/test2.svg").open() as f:
        assert f.read() == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="850" height="200" viewBox="0 0 850 200">\n<defs>\n</defs>\n<path d="M150,37.5 L170,37.5" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,37.5 L112.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M160.0,37.5 L282.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,25.0 L340,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M330.0,25.0 L415.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,12.5 L510,12.5" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M500.0,12.5 L547.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M500.0,12.5 L717.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="lightblue" />\n<rect x="170" y="0" width="150" height="50" fill="pink" />\n<rect x="0" y="100" width="150" height="50" fill="pink" />\n<rect x="170" y="100" width="150" height="50" fill="pink" />\n<rect x="340" y="0" width="150" height="50" fill="pink" />\n<rect x="340" y="100" width="150" height="50" fill="pink" />\n<rect x="510" y="0" width="150" height="50" fill="pink" />\n<rect x="510" y="100" width="150" height="50" fill="lightblue" />\n<rect x="680" y="100" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0007.html" target="_parent">[...]><text x="28.799999999999997" y="25.0" font-size="12">Владимир Путин</text>\n</a><a xlink:href="None/I0008.html" target="_parent">[...]><text x="188.9" y="25.0" font-size="12">Людмила Шкребнева</text>\n</a><a xlink:href="None/I0009.html" target="_parent">[...]><text x="35.4" y="125.0" font-size="12">Мария Путина</text>\n</a><a xlink:href="None/I0010.html" target="_parent">[...]><text x="195.5" y="125.0" font-size="12">Катерина Путина</text>\n</a><a xlink:href="None/I0011.html" target="_parent">[...]><text x="352.3" y="25.0" font-size="12">Светлана Кривоногих</text>\n</a><a xlink:href="None/I0012.html" target="_parent">[...]><text x="382.0" y="125.0" font-size="12">Елизавета </text>\n</a><a xlink:href="None/I0015.html" target="_parent">[...]><text x="542.1" y="25.0" font-size="12">Алина Кабаева</text>\n</a><a xlink:href="None/I0016.html" target="_parent">[...]><text x="552.0" y="125.0" font-size="12">Иван Путин</text>\n</a><a xlink:href="None/I0017.html" target="_parent">[...]><text x="708.8" y="125.0" font-size="12">Владимир Путин</text>\n</a></svg>'


def test_children_without_mother(_tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0002", gramps_tree=tree, output_path=Path("tmp/I0002.svg")
    )
    with Path("tmp/I0002.svg").open() as f:
        assert f.read() == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="340" height="300" viewBox="0 0 340 300">\n<defs>\n</defs>\n<path d="M150,25.0 L170,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M75.0,125.0 L75.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M75.0,125.0 L245.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="pink" />\n<rect x="170" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<rect x="0" y="200" width="150" height="50" fill="lightblue" />\n<rect x="170" y="200" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0001.html" target="_parent">[...]><text x="25.499999999999993" y="25.0" font-size="12">Людмила Иванова</text>\n</a><a xlink:href="None/I0004.html" target="_parent">[...]><text x="185.6" y="25.0" font-size="12">Анатолий Навальный</text>\n</a><a xlink:href="None/I0002.html" target="_parent">[...]><text x="28.799999999999997" y="125.0" font-size="12">Олег Навальный</text>\n</a><a xlink:href="None/I0018.html" target="_parent">[...]><text x="22.199999999999996" y="225.0" font-size="12">Степан Навальный</text>\n</a><a xlink:href="None/I0019.html" target="_parent">[...]><text x="195.5" y="225.0" font-size="12">Остап Навальный</text>\n</a></svg>'
