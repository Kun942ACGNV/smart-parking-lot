from __future__ import annotations

from typing import Dict, List


class TrieNode:
    def __init__(self) -> None:
        self.children: Dict[str, "TrieNode"] = {}
        self.is_end = False


class PlateTrie:
    """字典樹：車牌前綴搜尋。"""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, plate: str) -> None:
        node = self.root
        for ch in plate:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True

    def search_prefix(self, prefix: str) -> List[str]:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return []
            node = node.children[ch]
        result: List[str] = []

        def dfs(n: TrieNode, path: str) -> None:
            if n.is_end:
                result.append(prefix + path)
            for c in sorted(n.children):
                dfs(n.children[c], path + c)

        dfs(node, "")
        return result

    def delete(self, plate: str) -> None:
        def _del(node: TrieNode, i: int) -> bool:
            # 回傳 True 表示該節點可從父節點移除
            if i == len(plate):
                if not node.is_end:
                    return False
                node.is_end = False
                return not node.children
            child = node.children.get(plate[i])
            if child is None:
                return False
            if _del(child, i + 1):
                del node.children[plate[i]]
                return not node.children and not node.is_end
            return False

        _del(self.root, 0)
