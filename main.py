import sys

from agent import ask

MAX_HISTORY = 3


def main():
    print("文档知识库 Agent 已启动，输入 exit 退出")
    history = []
    while True:
        q = input("> ").strip()
        if q.lower() in ("exit", "quit"):
            break
        if not q:
            continue
        try:
            answer = ask(q, history)
        except Exception as e:
            print(f"\n[错误] {e}\n")
            continue
        print(f"\n{answer}\n")
        history.append({"role": "user", "content": q})
        history.append({"role": "assistant", "content": answer})
        history = history[-MAX_HISTORY * 2:]


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
