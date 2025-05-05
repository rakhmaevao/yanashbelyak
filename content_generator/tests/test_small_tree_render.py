import shutil
import sys

sys.path.append(".")

from pathlib import Path

import pytest
from src.gramps_tree import GrampsTree
from src.small_tree_render import SmallTreeRender, WithoutRelationsError


@pytest.fixture(scope="session")
def _tmp_dir():
    Path("tmp").mkdir(parents=True, exist_ok=True)
    yield
    shutil.rmtree("tmp")


@pytest.mark.usefixtures("_tmp_dir")
def test_normal_family() -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0000", gramps_tree=tree, output_path=Path("tmp/test1.svg")
    )
    with Path("tmp/test1.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="340" height="300" viewBox="0 0 340 300">\n<defs>\n</defs>\n<path d="M150,25.0 L170,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,125.0 L170,125.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,125.0 L75.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M160.0,125.0 L245.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="pink" />\n<rect x="170" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<rect x="170" y="100" width="150" height="50" fill="pink" />\n<rect x="0" y="200" width="150" height="50" fill="pink" />\n<rect x="170" y="200" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0001.html" target="_parent">[...]><text x="17.249999999999993" y="25.0" font-size="14">Людмила Иванова</text>\n</a><a xlink:href="None/I0004.html" target="_parent">[...]><text x="175.7" y="25.0" font-size="14">Анатолий Навальный</text>\n</a><a xlink:href="None/I0000.html" target="_parent">[...]><text x="9.549999999999997" y="125.0" font-size="14">Алексей Навальный</text>\n</a><a xlink:href="None/I0003.html" target="_parent">[...]><text x="187.25" y="125.0" font-size="14">Юлия Абросимова</text>\n</a><a xlink:href="None/I0005.html" target="_parent">[...]><text x="17.249999999999993" y="225.0" font-size="14">Дарья Навальная</text>\n</a><a xlink:href="None/I0006.html" target="_parent">[...]><text x="187.25" y="225.0" font-size="14">Захар Навальный</text>\n</a></svg>'
        )


@pytest.mark.usefixtures("_tmp_dir")
def test_without_relations() -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    with pytest.raises(WithoutRelationsError):
        render.create_svg(
            base_person_id="I0013", gramps_tree=tree, output_path=Path("tmp/I0013.svg")
        )


@pytest.mark.usefixtures("_tmp_dir")
def test_without_children() -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0006", gramps_tree=tree, output_path=Path("tmp/I0006.svg")
    )
    with Path("tmp/I0006.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="340" height="200" viewBox="0 0 340 200">\n<defs>\n</defs>\n<path d="M150,25.0 L170,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="pink" />\n<rect x="170" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0003.html" target="_parent">[...]><text x="17.249999999999993" y="25.0" font-size="14">Юлия Абросимова</text>\n</a><a xlink:href="None/I0000.html" target="_parent">[...]><text x="179.55" y="25.0" font-size="14">Алексей Навальный</text>\n</a><a xlink:href="None/I0006.html" target="_parent">[...]><text x="17.249999999999993" y="125.0" font-size="14">Захар Навальный</text>\n</a></svg>'
        )


@pytest.mark.usefixtures("_tmp_dir")
def test_only_parents() -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0000", gramps_tree=tree, output_path=Path("tmp/I0000.svg")
    )


@pytest.mark.usefixtures("_tmp_dir")
def test_many_womans() -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0007", gramps_tree=tree, output_path=Path("tmp/test2.svg")
    )
    with Path("tmp/test2.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="850" height="200" viewBox="0 0 850 200">\n<defs>\n</defs>\n<path d="M150,37.5 L170,37.5" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,37.5 L112.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M160.0,37.5 L282.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,25.0 L340,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M330.0,25.0 L415.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,12.5 L510,12.5" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M500.0,12.5 L547.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M500.0,12.5 L717.5,100" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="lightblue" />\n<rect x="170" y="0" width="150" height="50" fill="pink" />\n<rect x="0" y="100" width="150" height="50" fill="pink" />\n<rect x="170" y="100" width="150" height="50" fill="pink" />\n<rect x="340" y="0" width="150" height="50" fill="pink" />\n<rect x="340" y="100" width="150" height="50" fill="pink" />\n<rect x="510" y="0" width="150" height="50" fill="pink" />\n<rect x="510" y="100" width="150" height="50" fill="lightblue" />\n<rect x="680" y="100" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0007.html" target="_parent">[...]><text x="21.099999999999994" y="25.0" font-size="14">Владимир Путин</text>\n</a><a xlink:href="None/I0008.html" target="_parent">[...]><text x="179.55" y="25.0" font-size="14">Людмила Шкребнева</text>\n</a><a xlink:href="None/I0009.html" target="_parent">[...]><text x="28.799999999999997" y="125.0" font-size="14">Мария Путина</text>\n</a><a xlink:href="None/I0010.html" target="_parent">[...]><text x="187.25" y="125.0" font-size="14">Катерина Путина</text>\n</a><a xlink:href="None/I0011.html" target="_parent">[...]><text x="341.85" y="25.0" font-size="14">Светлана Кривоногих</text>\n</a><a xlink:href="None/I0012.html" target="_parent">[...]><text x="376.5" y="125.0" font-size="14">Елизавета </text>\n</a><a xlink:href="None/I0015.html" target="_parent">[...]><text x="534.95" y="25.0" font-size="14">Алина Кабаева</text>\n</a><a xlink:href="None/I0016.html" target="_parent">[...]><text x="546.5" y="125.0" font-size="14">Иван Путин</text>\n</a><a xlink:href="None/I0017.html" target="_parent">[...]><text x="701.1" y="125.0" font-size="14">Владимир Путин</text>\n</a></svg>'
        )


@pytest.mark.usefixtures("_tmp_dir")
def test_children_without_mother() -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0002", gramps_tree=tree, output_path=Path("tmp/I0002.svg")
    )
    with Path("tmp/I0002.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="340" height="300" viewBox="0 0 340 300">\n<defs>\n</defs>\n<path d="M150,25.0 L170,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M160.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M75.0,125.0 L75.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M75.0,125.0 L245.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="pink" />\n<rect x="170" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<rect x="0" y="200" width="150" height="50" fill="lightblue" />\n<rect x="170" y="200" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0001.html" target="_parent">[...]><text x="17.249999999999993" y="25.0" font-size="14">Людмила Иванова</text>\n</a><a xlink:href="None/I0004.html" target="_parent">[...]><text x="175.7" y="25.0" font-size="14">Анатолий Навальный</text>\n</a><a xlink:href="None/I0002.html" target="_parent">[...]><text x="21.099999999999994" y="125.0" font-size="14">Олег Навальный</text>\n</a><a xlink:href="None/I0018.html" target="_parent">[...]><text x="13.399999999999991" y="225.0" font-size="14">Степан Навальный</text>\n</a><a xlink:href="None/I0019.html" target="_parent">[...]><text x="187.25" y="225.0" font-size="14">Остап Навальный</text>\n</a></svg>'
        )
