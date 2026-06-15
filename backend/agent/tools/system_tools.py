"""
系统信息工具 — 让它知道自己有什么数据
"""

from langchain_core.tools import tool


@tool
def list_available_textbooks() -> dict:
    """列出你实际拥有的教材数据。回答"你有什么教材"之类问题时必须先调用此工具。"""
    from db import get_all_vector_dbs

    dbs = get_all_vector_dbs()
    textbooks = []
    for db in dbs:
        name = db["name"]
        # 格式化名称
        readable = name.replace("_", " ")
        textbooks.append({"id": name, "name": readable})

    return {
        "status": "success",
        "data": textbooks,
        "source": "local",
        "metadata": {"hint": "只回答这里列出的教材。如果没有某本教材，诚实告知用户。"},
    }
