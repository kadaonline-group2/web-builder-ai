import json
from app.services.llm_service import (
    ask_llm,
    revise_website_state,
    validate_website_state,
    GENERATE_SYSTEM_PROMPT,
)


def main():
    # 1. Generate initial website
    business = "Warung makan Bu Sari, menjual nasi goreng dan mie ayam"
    current_state = ask_llm(business, GENERATE_SYSTEM_PROMPT)
    print("Generated state:")
    print(json.dumps(current_state, indent=2))

    is_valid, error = validate_website_state(current_state)
    if not is_valid:
        print(f"\nValidation failed: {error}")
        return
    print("\nValidation passed!")

    # 2. Revise: change color
    current_state = revise_website_state(json.dumps(current_state), "Ganti warna utama jadi hijau toska")
    print("\nAfter revision (color):")
    print(json.dumps(current_state, indent=2))

    # 3. Revise: change text
    current_state = revise_website_state(json.dumps(current_state), "Ganti headline jadi 'Nasi Goreng Enak dan Murah'")
    print("\nAfter revision (text):")
    print(json.dumps(current_state, indent=2))


if __name__ == "__main__":
    main()
