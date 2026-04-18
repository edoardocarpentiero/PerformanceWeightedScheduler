from pathlib import Path
import re
import sys


MANAGER_PATH = Path("/opt/stack/cinder/cinder/volume/manager.py")


def insert_import(text: str) -> str:
    import_line = "from cinder.volume.collector_service import PerformanceCollectorService"
    import_marker = "# PLUGIN_IMPORT_PERFORMANCE_COLLECTOR"

    if import_marker in text:
        return text

    lines = text.splitlines()
    insert_idx = None

    # Prima prova vicino agli import di cinder.volume
    for i, line in enumerate(lines):
        if line.startswith("from cinder.volume import") or line.startswith("import cinder.volume"):
            insert_idx = i

    # Fallback: vicino agli import di cinder
    if insert_idx is None:
        for i, line in enumerate(lines):
            if line.startswith("from cinder import") or line.startswith("import cinder"):
                insert_idx = i

    if insert_idx is None:
        raise RuntimeError("Impossibile trovare un punto adatto per inserire l'import in manager.py")

    lines.insert(insert_idx + 1, f"{import_line} {import_marker}")
    return "\n".join(lines) + "\n"


def insert_helper_methods(text: str) -> str:
    helper_marker = "# PLUGIN_HELPERS_PERFORMANCE_COLLECTOR"

    if helper_marker in text:
        return text

    class_match = re.search(r'^class\s+VolumeManager\s*\([^)]*\):', text, re.MULTILINE)
    if not class_match:
        raise RuntimeError("Classe VolumeManager non trovata in manager.py")

    # Inseriamo subito dopo la definizione della classe
    insert_pos = class_match.end()

    helper_block = """
    # PLUGIN_HELPERS_PERFORMANCE_COLLECTOR
    def _run_performance_collector_on_init(self):
        try:
            collector = PerformanceCollectorService()
            collector.update_all_backend_metrics(context.get_admin_context())
        except Exception as exc:
            LOG.warning("Performance Collector init_host failed: %s", exc)

    def _run_performance_collector_on_create(self, context):
        try:
            collector = PerformanceCollectorService()
            collector.update_all_backend_metrics(context)
        except Exception as exc:
            LOG.warning("Performance Collector create_volume failed: %s", exc)
""".rstrip("\n")

    return text[:insert_pos] + "\n\n" + helper_block + text[insert_pos:]


def _insert_call_into_method(text: str, method_name: str, call_line: str, marker: str) -> str:
    if marker in text:
        return text

    lines = text.splitlines()

    # Cerca la definizione del metodo
    def_idx = None
    for i, line in enumerate(lines):
        if re.match(rf'^\s*def\s+{re.escape(method_name)}\s*\(', line):
            def_idx = i
            break

    if def_idx is None:
        raise RuntimeError(f"Metodo {method_name} non trovato in manager.py")

    # Trova la prima riga del corpo con contenuto reale
    body_idx = None
    body_indent = None

    for j in range(def_idx + 1, len(lines)):
        line = lines[j]

        # Salta righe vuote
        if not line.strip():
            continue

        # Calcola indentazione
        indent = len(line) - len(line.lstrip(" "))

        # Se la riga è più indentata della def, è corpo del metodo
        def_indent = len(lines[def_idx]) - len(lines[def_idx].lstrip(" "))
        if indent > def_indent:
            body_idx = j
            body_indent = " " * indent
            break

        # Se siamo arrivati a una riga con indentazione <= def, il corpo non è stato trovato
        if indent <= def_indent:
            break

    if body_idx is None or body_indent is None:
        raise RuntimeError(f"Impossibile determinare il corpo del metodo {method_name}")

    lines.insert(body_idx, f"{body_indent}{call_line}  {marker}")
    return "\n".join(lines) + "\n"


def patch_manager() -> None:
    if not MANAGER_PATH.exists():
        raise RuntimeError(f"manager.py non trovato: {MANAGER_PATH}")

    text = MANAGER_PATH.read_text(encoding="utf-8")

    text = insert_import(text)
    text = insert_helper_methods(text)

    text = _insert_call_into_method(
        text=text,
        method_name="init_host",
        call_line="self._run_performance_collector_on_init()",
        marker="# PLUGIN_INIT_PERFORMANCE_COLLECTOR",
    )

    text = _insert_call_into_method(
        text=text,
        method_name="create_volume",
        call_line="self._run_performance_collector_on_create(context)",
        marker="# PLUGIN_CREATE_PERFORMANCE_COLLECTOR",
    )

    MANAGER_PATH.write_text(text, encoding="utf-8")


def main() -> int:
    try:
        patch_manager()
        print("manager.py patchato correttamente")
        return 0
    except Exception as exc:
        print(f"[ERRORE] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())