"""
DocumentCompass MCP Server - 智能文档导航系统
让 LLM 像人一样分段阅读超长文档
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from xml.etree import ElementTree as ET


@dataclass
class DocumentNode:
    """文档节点 - 类似 DOM 节点"""

    type: str  # heading, paragraph, list, code, etc.
    level: Optional[int] = None  # for headings
    id: str = ""
    title: str = ""
    content: str = ""
    attributes: Dict[str, Any] = {}
    children: List["DocumentNode"] = []
    parent: Optional["DocumentNode"] = None

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}
        if self.children is None:
            self.children = []


class DocumentCompass:
    """文档指南针 - 核心导航引擎"""

    def __init__(self, source_text: str, source_format: str = "markdown"):
        self.source_text = source_text
        self.source_format = source_format
        self.root = self._parse_document()
        self.index = self._build_index()

    def _parse_document(self) -> DocumentNode:
        """解析文档为树状结构"""
        if self.source_format == "markdown":
            return self._parse_markdown()
        elif self.source_format == "xml":
            return self._parse_xml()
        else:
            raise ValueError(f"Unsupported format: {self.source_format}")

    def _parse_xml(self) -> DocumentNode:
        """解析 XML 为 DOM 树"""
        root = DocumentNode(type="document", id="root")
        xml_root = ET.fromstring(self.source_text)
        
        def process_element(element, parent_node):
            for child in element:
                node = DocumentNode(
                    type=child.tag,
                    id=child.get("id", f"xml_{len(parent_node.children)}"),
                    content=child.text if child.text else "",
                    attributes=child.attrib,
                    parent=parent_node
                )
                parent_node.children.append(node)
                process_element(child, node)
                
        process_element(xml_root, root)
        return root

    def _parse_markdown(self) -> DocumentNode:
        """解析 Markdown 为 DOM 树"""
        root = DocumentNode(type="document", id="root")
        lines = self.source_text.split("\n")

        current_parents = [root]  # 栈结构追踪父节点
        node_counter = 0

        for line_num, line in enumerate(lines):
            # 标题解析
            heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                node_id = f"h{level}_{node_counter}"

                # 调整父节点栈
                while len(current_parents) > level:
                    current_parents.pop()

                heading_node = DocumentNode(
                    type="heading",
                    level=level,
                    id=node_id,
                    title=title,
                    content=line,
                    attributes={"line_number": line_num},
                )

                current_parents[-1].children.append(heading_node)
                heading_node.parent = current_parents[-1]
                current_parents.append(heading_node)
                node_counter += 1
                continue

            # 段落解析
            if line.strip():
                para_node = DocumentNode(
                    type="paragraph",
                    id=f"p_{node_counter}",
                    content=line,
                    attributes={"line_number": line_num},
                )
                current_parents[-1].children.append(para_node)
                para_node.parent = current_parents[-1]
                node_counter += 1

        return root

    def _build_index(self) -> Dict[str, DocumentNode]:
        """构建索引 - 类似 getElementById"""
        index = {}

        def traverse(node):
            if node.id:
                index[node.id] = node
            for child in node.children:
                traverse(child)

        traverse(self.root)
        return index

    # === MCP Server 核心方法 ===

    def get_outline(self, max_depth: int = 3) -> str:
        """获取文档大纲"""
        outline = []

        def build_outline(node, depth=0):
            if depth > max_depth:
                return

            if node.type == "heading":
                indent = "  " * (depth - 1) if depth > 0 else ""
                outline.append(f"{indent}- {node.title} (#{node.id})")

            for child in node.children:
                build_outline(child, depth + 1 if node.type == "heading" else depth)

        build_outline(self.root)
        return "\n".join(outline)

    def get_section(self, node_id: str, include_subsections: bool = True) -> str:
        """获取指定节点内容"""
        if node_id not in self.index:
            return f"Section '{node_id}' not found"

        node = self.index[node_id]
        content = [node.content] if node.content else []

        if include_subsections:

            def collect_content(n):
                for child in n.children:
                    if child.content:
                        content.append(child.content)
                    if child.type == "heading" and child.level > node.level:
                        content.append(child.content)
                    collect_content(child)

            collect_content(node)

        return "\n".join(content)

    def search(self, query: str, context_lines: int = 2) -> List[Dict]:
        """搜索文档内容"""
        results = []

        def search_node(node):
            if query.lower() in node.content.lower():
                # 查找最近的标题作为上下文
                parent = node.parent
                while parent and parent.type != "heading":
                    parent = parent.parent

                section_title = parent.title if parent else "Document Root"

                results.append(
                    {
                        "node_id": node.id,
                        "section": section_title,
                        "section_id": parent.id if parent else "root",
                        "content": node.content,
                        "type": node.type,
                    }
                )

            for child in node.children:
                search_node(child)

        search_node(self.root)
        return results

    def get_navigation_context(self, node_id: str) -> Dict:
        """获取导航上下文 - 前后节点信息"""
        if node_id not in self.index:
            return {"error": "Node not found"}

        node = self.index[node_id]
        parent = node.parent

        context = {
            "current": {"id": node.id, "title": node.title, "type": node.type},
            "parent": None,
            "siblings": [],
            "children": [],
        }

        if parent:
            context["parent"] = {"id": parent.id, "title": parent.title}

            # 同级节点
            for sibling in parent.children:
                if sibling.type == "heading":
                    context["siblings"].append(
                        {
                            "id": sibling.id,
                            "title": sibling.title,
                            "is_current": sibling.id == node.id,
                        }
                    )

        # 子节点
        for child in node.children:
            if child.type == "heading":
                context["children"].append({"id": child.id, "title": child.title})

        return context

    def query_by_xpath(self, xpath: str) -> List[DocumentNode]:
        """类 XPath 查询"""
        # 简化的 XPath 实现
        # 例如: "//heading[@level='1']" 或 "//heading[title='Introduction']"
        results = []

        def matches_xpath(node, path_parts):
            if not path_parts:
                return True

            current_part = path_parts[0]
            remaining_parts = path_parts[1:]

            if current_part.startswith("//"):
                # 递归搜索
                node_type = current_part[2:]
                if node.type == node_type:
                    if matches_xpath(node, remaining_parts):
                        return True

                for child in node.children:
                    if matches_xpath(child, path_parts):
                        return True

            return False

        # 简化实现，可以扩展更复杂的 XPath 语法
        return results


# === MCP Server 接口实现 ===


class DocumentCompassMCP:
    """MCP Server 接口"""

    def __init__(self):
        self.documents: Dict[str, DocumentCompass] = {}

    def load_document(self, doc_id: str, content: str, format: str = "markdown") -> str:
        """加载文档"""
        try:
            self.documents[doc_id] = DocumentCompass(content, format)
            return f"Document '{doc_id}' loaded successfully"
        except Exception as e:
            return f"Error loading document: {str(e)}"

    def get_outline(self, doc_id: str, max_depth: int = 3) -> str:
        """获取文档大纲"""
        if doc_id not in self.documents:
            return f"Document '{doc_id}' not found"
        return self.documents[doc_id].get_outline(max_depth)

    def read_section(self, doc_id: str, section_id: str) -> str:
        """读取指定章节"""
        if doc_id not in self.documents:
            return f"Document '{doc_id}' not found"
        return self.documents[doc_id].get_section(section_id)

    def search_document(self, doc_id: str, query: str) -> str:
        """搜索文档"""
        if doc_id not in self.documents:
            return f"Document '{doc_id}' not found"

        results = self.documents[doc_id].search(query)
        if not results:
            return f"No results found for '{query}'"

        output = f"Found {len(results)} results for '{query}':\n\n"
        for i, result in enumerate(results[:5], 1):  # 限制显示前5个结果
            output += (
                f"{i}. In section '{result['section']}' (#{result['section_id']}):\n"
            )
            output += f"   {result['content'][:100]}...\n\n"

        return output

    def navigate(self, doc_id: str, section_id: str) -> str:
        """获取导航上下文"""
        if doc_id not in self.documents:
            return f"Document '{doc_id}' not found"

        context = self.documents[doc_id].get_navigation_context(section_id)
        if "error" in context:
            return context["error"]

        output = f"Current: {context['current']['title']}\n"

        if context["parent"]:
            output += f"Parent: {context['parent']['title']}\n"

        if context["siblings"]:
            output += "Siblings:\n"
            for sibling in context["siblings"]:
                marker = "→ " if sibling["is_current"] else "  "
                output += f"{marker}{sibling['title']} (#{sibling['id']})\n"

        if context["children"]:
            output += "Subsections:\n"
            for child in context["children"]:
                output += f"  {child['title']} (#{child['id']})\n"

        return output


# 使用示例
if __name__ == "__main__":
    # 示例 Markdown 文档
    sample_doc = """
# Introduction
This is the introduction to our document.

## Getting Started
Here's how to get started.

### Prerequisites
You need these things first.

### Installation
Follow these steps to install.

## Advanced Topics
More complex stuff here.

### Configuration
How to configure the system.

### Troubleshooting
Common problems and solutions.

# Conclusion
That's all folks!
"""

    # 创建 MCP 服务器
    mcp = DocumentCompassMCP()

    # 加载文档
    print(mcp.load_document("sample", sample_doc))
    print("\n" + "=" * 50 + "\n")

    # 获取大纲
    print("OUTLINE:")
    print(mcp.get_outline("sample"))
    print("\n" + "=" * 50 + "\n")

    # 读取特定章节
    print("SECTION h1_0:")
    print(mcp.read_section("sample", "h1_0"))
    print("\n" + "=" * 50 + "\n")

    # 搜索
    print("SEARCH 'install':")
    print(mcp.search_document("sample", "install"))
    print("\n" + "=" * 50 + "\n")

    # 导航
    print("NAVIGATION for h2_1:")
    print(mcp.navigate("sample", "h2_1"))
