"""
计算工具 — Python math 安全沙箱
处理时区、比例尺、太阳高度角等地理计算
"""

import math
from langchain_core.tools import tool

# 预置地理公式
GEO_FORMULAS = {
    # 时区差: timezone_diff(东经, 西经) → 小时
    "timezone_diff": lambda lon1, lon2: abs(lon1 - lon2) / 15,
    # 比例尺: scale_distance(图上cm, 比例尺分母) → 实际km
    "scale_distance": lambda map_cm, denominator: (map_cm * denominator) / 100000,
    # 正午太阳高度角: solar_angle(纬度, 太阳直射点纬度)
    "solar_angle": lambda lat, decl: 90 - abs(lat - decl),
    # 人口密度: density(人口数, 面积km²)
    "population_density": lambda pop, area: pop / area,
}

# 安全命名空间
_SAFE_NS = {
    **GEO_FORMULAS,
    "math": math,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "radians": math.radians, "degrees": math.degrees,
    "pi": math.pi, "abs": abs, "round": round,
}


@tool
def calculate(expression: str, calc_type: str = "general") -> dict:
    """执行地理相关的数学计算。所有涉及数值的计算必须通过此工具，不要手动计算。

    支持的计算类型：
    - timezone: 时区换算，使用 timezone_diff(lon1, lon2)
    - scale: 比例尺换算，使用 scale_distance(cm, denominator)
    - solar_angle: 太阳高度角，使用 solar_angle(lat, decl)
    - density: 人口/资源密度
    - general: 通用计算（加减乘除）

    Args:
        expression: 计算表达式，如 "timezone_diff(120, -75)" 或 "120 / 15"
        calc_type: 计算类型

    Returns:
        {"status": "success", "data": {"expression": "...", "result": 8}, "source": "computed"}
    """
    try:
        result = eval(expression, {"__builtins__": {}}, _SAFE_NS)
        return {
            "status": "success",
            "data": {"expression": expression, "result": result},
            "source": "computed",
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "source": "computed"}
