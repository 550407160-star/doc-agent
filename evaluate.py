import json
import sys
from pathlib import Path

from openai import OpenAI

from agent import ask
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

JUDGE_PROMPT = """你是严格的评测员。根据问题、参考答案与模型回答，从三个维度打分(1-5整数)：
- relevance: 回答与问题的相关程度
- faithfulness: 回答是否忠实于检索到的知识库内容，是否存在幻觉
- helpfulness: 回答是否完整、正确、有用

只输出JSON，格式：{{"relevance": n, "faithfulness": n, "helpfulness": n}}
问题：{question}
参考答案：{reference}
模型回答：{answer}"""


def judge(question, reference, answer):
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(question=question, reference=reference, answer=answer)}],
    )
    text = resp.choices[0].message.content.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


def main():
    if len(sys.argv) < 2:
        print("用法: python evaluate.py <问题集json路径>")
        return
    questions = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows = []
    for i, item in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] 评测中: {item['question']}")
        answer = ask(item["question"])
        scores = judge(item["question"], item.get("reference", ""), answer)
        rows.append({"question": item["question"], "answer": answer, **scores})
        print(f"  -> {scores}")
    avg = {k: round(sum(r[k] for r in rows) / len(rows), 2) for k in ("relevance", "faithfulness", "helpfulness")}
    report = {"avg_scores": avg, "results": rows}
    Path("report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n平均分: {avg}")
    print("报告已保存: report.json")


if __name__ == "__main__":
    main()
