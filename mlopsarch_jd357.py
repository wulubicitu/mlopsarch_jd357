"""mlopsarch_jd357 —— 按权重把MLOps 平台架构师·混合检索的权重调节的额度分配到各项。

按给定权重把总额度分配到各项，报告超分配项与利用率

定位：
  超分配要显式报出来，而不是让分配结果静默超过总额度

岗位对应：
  目标岗位　京东 · 负责人MLOps 平台架构师
  技能主线　MLOps、Kubernetes、Docker、Python
  领域标签　MLOps、AI基础设施

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到岗位要求的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python mlopsarch_jd357.py --help
    python mlopsarch_jd357.py --file input.txt
    python mlopsarch_jd357.py --text "示例内容"
    python mlopsarch_jd357.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 岗位规则表：每条规则独立可核查，命中即报，不做推断。
# 规则由岗位 JD 的技能线与领域标签派生——每条都能对回岗位要求。
# 目标岗位：京东 · 负责人MLOps 平台架构师
RULES: list[dict] = [
    {
        "name": "MLOps 平台架构师·混合检索的权重调节·缺失",
        "why": "岗位要求「MLOps」在输入里找不到对应内容",
        "severity": "high",
        "keywords": ['missing', 'absent', '缺少', '没有', '未提供', 'MLOps'],
    },
    {
        "name": "MLOps 平台架构师·混合检索的权重调节·冲突",
        "why": "两处关于「Kubernetes」的描述互相矛盾",
        "severity": "high",
        "keywords": ['conflict', 'contradict', '矛盾', '不一致', '相反', 'Kubernetes'],
    },
    {
        "name": "MLOps 平台架构师·混合检索的权重调节·越界",
        "why": "「Docker」的取值超出岗位场景的常规范围",
        "severity": "medium",
        "keywords": ['out of range', 'outlier', '越界', '超限', '超过', 'Docker'],
    },
    {
        "name": "MLOps 平台架构师·混合检索的权重调节·退化",
        "why": "「Python」相关的信息量不足以支撑判断",
        "severity": "medium",
        "keywords": ['degrade', 'insufficient', '不足', '太少', '无法', 'Python'],
    },
    {
        "name": "MLOps 平台架构师·混合检索的权重调节·泄漏",
        "why": "「AI基础设施」相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['leak', 'expose', '泄漏', '暴露', '明文', 'AI基础设施'],
    },
    {
        "name": "MLOps 平台架构师·混合检索的权重调节·重复",
        "why": "同一处「MLOps 平台架构师」信息被反复传递",
        "severity": "low",
        "keywords": ['duplicate', 'repeat', '重复', 'again', 'MLOps 平台架构师'],
    },
    {
        "name": "MLOps 平台架构师·混合检索的权重调节·陈旧#2",
        "why": "「MLOps」的时效性已过期",
        "severity": "medium",
        "keywords": ['stale', 'expired', '过期', '陈旧', '旧版', 'MLOps'],
    },
    {
        "name": "MLOps 平台架构师·混合检索的权重调节·不可核#2",
        "why": "关于「Kubernetes」的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['unverifiable', 'no evidence', '无法追溯', '没有来源', 'Kubernetes'],
    },
]


def mlopsarch_jd357_read_numbers(text: str) -> list[float]:
    return [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))]


def mlopsarch_jd357_allocate(total: float, weights: list[float]) -> list[float]:
    """按权重分配预算，权重和为 0 时均分。"""
    if not weights:
        return []
    s = sum(weights)
    if s == 0:
        return [total / len(weights)] * len(weights)
    return [total * w / s for w in weights]


def mlopsarch_jd357_analyze(text: str) -> dict:
    """主分析：预算分配与消耗核对。"""
    nums = mlopsarch_jd357_read_numbers(text)
    if not nums:
        return {"ok": False, "error": "文本里没有数字", "count": 0}
    total = nums[0]
    weights = nums[1:] if len(nums) > 1 else [1.0]
    alloc = mlopsarch_jd357_allocate(total, weights)
    consumed = sum(alloc)
    over = [i for i, a in enumerate(alloc) if a > total and total > 0]
    return {
        "ok": True,
        "total": total,
        "weight_count": len(weights),
        "allocation": [round(a, 4) for a in alloc],
        "consumed": round(consumed, 4),
        "remaining": round(total - consumed, 4),
        "over_allocated": over,
        "utilization": round(consumed / total, 4) if total else 0.0,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"总预算：{result['total']}  权重项：{result['weight_count']}")
    out.append("")
    for i, a in enumerate(result["allocation"]):
        out.append(f"  #{i}  {a}")
    out.append("")
    out.append(f"已分配 {result['consumed']}  剩余 {result['remaining']}  利用率 {result['utilization']:.2%}")
    if result["over_allocated"]:
        out.append(f"超分配的项：{result['over_allocated']}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="mlopsarch_jd357",
        description="按给定权重把总额度分配到各项，报告超分配项与利用率（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python mlopsarch_jd357.py --file input.txt\n"
            "  python mlopsarch_jd357.py --text '示例内容'\n"
            "  python mlopsarch_jd357.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = mlopsarch_jd357_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
