from pathlib import Path
import sys


MANAGER_PATH = Path("/opt/stack/cinder/cinder/volume/manager.py")


IMPORT_MARKER = "# PLUGIN_IMPORT_PERFORMANCE_COLLECTOR"
HELPER_MARKER = "# PLUGIN_HELPERS_PERFORMANCE_COLLECTOR"
INIT_MARKER = "# PLUGIN_INIT_PERFORMANCE_COLLECTOR"
CREATE_MARKER = "# PLUGIN_CREATE_PERFORMANCE_COLLECTOR"


def remove_marked_import(lines: list[str]) -> list[str]:
    return [line for line in lines if IMPORT_MARKER not in line]


def remove_marked_calls(lines: list[str]) -> list[str]:
    filtered = []
    for line in lines:
        if INIT_MARKER in line:
            continue
        if CREATE_MARKER in line:
            continue
        filtered.append(line)
    return filtered


def remove_helper_block(lines: list[str]) -> list[str]:
    """
    Rimuove il blocco helper introdotto dal plugin.
    Parte dalla riga con HELPER_MARKER e continua fino al termine
    delle due funzioni helper.
    """
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]

        if HELPER_MARKER in line:
            # Salta il marker
            i += 1

            # Salta tutte le righe successive che appartengono ai metodi helper,
            # finché restano indentate come metodi della classe o vuote.
            while i < len(lines):
                current = lines[i]

                # Se troviamo una riga vuota, continuiamo a saltarla
                if not current.strip():
                    i += 1
                    continue

                # I metodi helper sono indentati di 4 spazi
                # Le loro righe interne di 8+ spazi
                # Quando troviamo una nuova riga non indentata come metodo di classe,
                # usciamo dal blocco.
                if current.startswith("    ") and not current.startswith("class "):
                    i += 1
                    continue

                break

            continue

        result.append(line)
        i += 1

    return result


def cleanup_extra_blank_lines(lines: list[str]) -> list[str]:
    cleaned = []
    blank_count = 0

    for line in lines:
        if line.strip() == "":
            blank_count += 1
        else:
            blank_count = 0

        if blank_count <= 2:
            cleaned.append(line)

    return cleaned


def unpatch_manager() -> None:
    if not MANAGER_PATH.exists():
        raise RuntimeError(f"manager.py non trovato: {MANAGER_PATH}")

    text = MANAGER_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    lines = remove_marked_import(lines)
    lines = remove_marked_calls(lines)
    lines = remove_helper_block(lines)
    lines = cleanup_extra_blank_lines(lines)

    MANAGER_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    try:
        unpatch_manager()
        print("manager.py ripulito correttamente dai marker del plugin")
        return 0
    except Exception as exc:
        print(f"[ERRORE] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())