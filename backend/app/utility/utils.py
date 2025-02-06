def normalize_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")

def denormalize_name(name: str) -> str:
    return name.replace("_", " ").title()