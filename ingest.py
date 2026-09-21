import tools


def main():
    total = tools.ingest_dir()
    print(f"\n入库完成，共 {total} 个文本块")
    print("启动问答: python main.py")


if __name__ == "__main__":
    main()
