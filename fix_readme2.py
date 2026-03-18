with open("README.md", "r") as f:
    content = f.read()

content = content.replace(
    "- Fase 7 — Construcao do tenant demonstrativo ficticio",
    "- Fase 7 — Construcao do tenant demonstrativo ficticio"
)

old_text = "400-* Fase 8 — Construção da base documental fictícia e ingest limpa"
# Just verifying, the task asks to update overall docs. Using phase names. README has them.
