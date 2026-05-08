from pathlib import Path

from dotenv import find_dotenv


def set_env_values(values: dict[str, str]) -> None:
    env_path = find_dotenv(".env", usecwd=True) or ".env"
    path = Path(env_path)

    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    updated_keys: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else ""
        if key in values:
            new_lines.append(f"{key}={values[key]}")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    for key, value in values.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
