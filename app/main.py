from app.services.llm_service import ask_llm


def main():
    response = ask_llm("Say hello in one sentence.")
    print(response)


if __name__ == "__main__":
    main()
