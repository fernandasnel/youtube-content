"""
modules/utils.py
Helpers de CLI: banner, inputs, formatação.
"""


def banner():
    print("""
╔══════════════════════════════════════════════════╗
║         SEO Agent — YouTube → Blog Post          ║
║              Hotmart Blog  •  v1.0               ║
╚══════════════════════════════════════════════════╝""")


def ask_choice(question: str, options: list[str]) -> str:
    print(f"\n{question}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        choice = input(f"Escolha (1-{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print(f"  Digite um número entre 1 e {len(options)}")


def ask_yes_no(question: str) -> bool:
    while True:
        ans = input(f"{question} (s/n): ").strip().lower()
        if ans in ("s", "sim", "y", "yes"):
            return True
        if ans in ("n", "nao", "não", "no"):
            return False
        print("  Digite s ou n")
