import json
from app.services.llm_service import (
    generate_website_state,
    revise_website_state,
)


def main():
    business = "Warung makan Bu Sari, menjual nasi goreng dan mie ayam"
    current_state, is_fallback = generate_website_state(business)

    if is_fallback:
        print("Generated with fallback defaults")

    print("Generated state:")
    print(json.dumps(current_state, indent=2))

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
