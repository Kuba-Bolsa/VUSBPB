from dataclasses import dataclass, field
from typing import List, Iterable


@dataclass
class TreeNode:
    label: str
    children: List["TreeNode"] = field(default_factory=list)


def renderTree(rootLabel: str, roots: Iterable[TreeNode]) -> str:
    lines: List[str] = [rootLabel]
    rootsList = list(roots)

    if not rootsList:
        lines.append("└── (empty)")
        return "\n".join(lines)

    lastIndex = len(rootsList) - 1
    for idx, root in enumerate(rootsList):
        helperRenderNode(root, prefix = "", isLast = (idx == lastIndex), lines = lines)

    return "\n".join(lines)


# Helpers
def helperRenderNode(node: TreeNode, prefix: str, isLast: bool, lines: List[str]) -> None:
    asciiConnector = "└── " if isLast else "├── "
    lines.append(f"{prefix}{asciiConnector}{node.label}")

    if not node.children:
        return

    childPrefix = prefix + ("    " if isLast else "│   ")
    lastIndex = len(node.children) - 1

    for idx, child in enumerate(node.children):
        helperRenderNode(child, childPrefix, idx == lastIndex, lines)