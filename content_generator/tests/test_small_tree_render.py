import shutil
import sys
sys.path.append(".")

import os
from pathlib import Path
import pytest
from src.gramps_tree import GrampsTree
from src.small_tree_render.small_tree_render import SmallTreeRender


@pytest.fixture
def tmp_dir():
    os.makedirs("tmp", exist_ok=True)
    yield
    shutil.rmtree("tmp")


def test_main(tmp_dir) -> None:
    tree = GrampsTree("tests/test_tree")
    render = SmallTreeRender()
    render.create_svg(
        base_person_id="I0000", gramps_tree=tree, output_path=Path("tmp/test.svg")
    )
    with Path("tmp/test.svg").open() as f:
        assert (
            f.read()
            == '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"\n     width="400" height="300" viewBox="0 0 400 300">\n<defs>\n</defs>\n<path d="M150,25.0 L200,25.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M175.0,25.0 L75.0,100" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M150,125.0 L200,125.0" stroke="black" stroke-width="0.8" fill="none" />\n<path d="M175.0,125.0 L75.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<path d="M175.0,125.0 L275.0,200" stroke="gray" stroke-width="0.8" fill="none" />\n<rect x="0" y="0" width="150" height="50" fill="pink" />\n<rect x="200" y="0" width="150" height="50" fill="lightblue" />\n<rect x="0" y="100" width="150" height="50" fill="lightblue" />\n<rect x="200" y="100" width="150" height="50" fill="pink" />\n<rect x="0" y="200" width="150" height="50" fill="pink" />\n<rect x="200" y="200" width="150" height="50" fill="lightblue" />\n<a xlink:href="None/I0001.html" target="_parent">[...]><text x="12.000000000000014" y="25.0" font-size="12">Людмила Иванова</text>\n</a><a xlink:href="None/I0004.html" target="_parent">[...]><text x="199.4" y="25.0" font-size="12">Анатолий Навальный</text>\n</a><a xlink:href="None/I0000.html" target="_parent">[...]><text x="3.6000000000000085" y="125.0" font-size="12">Алексей Навальный</text>\n</a><a xlink:href="None/I0003.html" target="_parent">[...]><text x="212.0" y="125.0" font-size="12">Юлия Абросимова</text>\n</a><a xlink:href="None/I0005.html" target="_parent">[...]><text x="12.000000000000014" y="225.0" font-size="12">Дарья Навальная</text>\n</a><a xlink:href="None/I0006.html" target="_parent">[...]><text x="212.0" y="225.0" font-size="12">Захар Навальный</text>\n</a></svg>'
        )
