from pathlib import Path
from content_generator.gramps_tree import GrampsTree
from content_generator.small_tree_render.small_tree_render import SmallTreeRender


def test_main() -> None:
    tree = GrampsTree()
    render = SmallTreeRender()
    render.create_svg(base_person_id="I0052", gramps_tree=tree, output_path=Path("test.svg"))