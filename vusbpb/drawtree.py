from dataclasses import dataclass, field
from typing import List, Iterable


@dataclass
class TreeNode:
    label: str
    children: List["TreeNode"] = field(default_factory=list)


def _render_node(node: TreeNode, prefix: str, is_last: bool, lines: List[str]) -> None:
    connector = "└── " if is_last else "├── "
    lines.append(f"{prefix}{connector}{node.label}")

    if not node.children:
        return

    child_prefix = prefix + ("    " if is_last else "│   ")
    last_index = len(node.children) - 1

    for idx, child in enumerate(node.children):
        _render_node(child, child_prefix, idx == last_index, lines)


def renderTree(root_label: str, roots: Iterable[TreeNode]) -> str:
    lines: List[str] = [root_label]
    roots_list = list(roots)

    if not roots_list:
        lines.append("└── (empty)")
        return "\n".join(lines)

    last_index = len(roots_list) - 1
    for idx, root in enumerate(roots_list):
        _render_node(root, prefix="", is_last=(idx == last_index), lines=lines)

    return "\n".join(lines)
