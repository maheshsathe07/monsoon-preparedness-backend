from pathlib import Path


ENV_PATH = Path(".env")


def main() -> int:
    if not ENV_PATH.exists():
        print(".env not found")
        return 1

    ok = True
    for line_no, line in enumerate(ENV_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            print(f"Line {line_no}: missing '='")
            ok = False
            continue
        key = stripped.split("=", 1)[0].strip()
        if not key.replace("_", "").isalnum() or not (key[0].isalpha() or key[0] == "_"):
            print(f"Line {line_no}: invalid key name")
            ok = False
    if ok:
        print(".env format looks valid")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
