from pathlib import Path
import re
import sys


MANAGER_PATH = Path("/opt/stack/cinder/cinder/volume/manager.py")


def insert_import(text: str) -> str:
    import_line = (
        "from cinder.volume.performance_weighted_scheduler_module1.collector_service "
        "import PerformanceCollectorService"
    )
    import_marker = "# PLUGIN_IMPORT_PERFORMANCE_COLLECTOR"

    if import_marker in text:
        return text

    lines = text.splitlines()
    insert_idx = None

    for i, line in enumerate(lines):
        if line.startswith("from cinder.volume import") or line.startswith("import cinder.volume"):
            insert_idx = i

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

    insert_pos = class_match.end()

    helper_block = """
    # PLUGIN_HELPERS_PERFORMANCE_COLLECTOR
    def _run_performance_collector_on_init(self):
        try:
            collector = PerformanceCollectorService()
            collector.update_current_backend_metrics(
                context.get_admin_context(),
                self.configuration,
                self.backend_name,
            )
        except Exception as exc:
            LOG.warning("Performance Collector init_host failed: %s", exc)

    def _run_performance_collector_on_create(self, context):
        try:
            collector = PerformanceCollectorService()
            collector.update_current_backend_metrics(
                context,
                self.configuration,
                self.backend_name,
            )
        except Exception as exc:
            LOG.warning("Performance Collector create_volume failed: %s", exc)
""".rstrip("\n")

    return text[:insert_pos] + "\n\n" + helper_block + text[insert_pos:]


def _find_method_signature_end(lines: list[str], start_idx: int) -> int:
    paren_balance = 0
    seen_open = False

    for i in range(start_idx, len(lines)):
        line = lines[i]

        for ch in line:
            if ch == "(":
                paren_balance += 1
                seen_open = True
            elif ch == ")":
                paren_balance -= 1

        if seen_open and paren_balance == 0 and line.strip().endswith(":"):
            return i

    raise RuntimeError("Impossibile trovare la fine della firma del metodo")


def _insert_call_after_signature(text: str, method_name: str, call_line: str, marker: str) -> str:
    if marker in text:
        return text

    lines = text.splitlines()

    start_idx = None
    def_indent = None

    for i, line in enumerate(lines):
        if re.match(rf'^(\s*)def\s+{re.escape(method_name)}\s*\(', line):
            start_idx = i
            def_indent = len(line) - len(line.lstrip(" "))
            break

    if start_idx is None:
        raise RuntimeError(f"Metodo {method_name} non trovato in manager.py")

    end_sig_idx = _find_method_signature_end(lines, start_idx)
    body_indent = " " * (def_indent + 4)
    lines.insert(end_sig_idx + 1, f"{body_indent}{call_line}  {marker}")

    return "\n".join(lines) + "\n"


def _insert_call_before_last_return_in_create(text: str, marker: str) -> str:
    if marker in text:
        return text

    lines = text.splitlines()

    start_idx = None
    def_indent = None

    for i, line in enumerate(lines):
        if re.match(r'^\s*def\s+create_volume\s*\(', line):
            start_idx = i
            def_indent = len(line) - len(line.lstrip(" "))
            break

    if start_idx is None:
        raise RuntimeError("Metodo create_volume non trovato in manager.py")

    end_sig_idx = _find_method_signature_end(lines, start_idx)
    body_indent = " " * (def_indent + 4)
    insert_idx = None

    for j in range(len(lines) - 1, end_sig_idx, -1):
        line = lines[j]
        current_indent = len(line) - len(line.lstrip(" "))

        if line.strip().startswith("def ") and current_indent <= def_indent:
            break
        if line.strip().startswith("class ") and current_indent <= def_indent:
            break

        if current_indent == def_indent + 4 and line.lstrip().startswith("return "):
            insert_idx = j
            break

    if insert_idx is None:
        raise RuntimeError("Impossibile trovare il return finale in create_volume")

    lines.insert(
        insert_idx,
        f"{body_indent}self._run_performance_collector_on_create(context)  {marker}",
    )

    return "\n".join(lines) + "\n"


def patch_manager() -> None:
    if not MANAGER_PATH.exists():
        raise RuntimeError(f"manager.py non trovato: {MANAGER_PATH}")

    text = MANAGER_PATH.read_text(encoding="utf-8")

    text = insert_import(text)
    text = insert_helper_methods(text)

    text = _insert_call_after_signature(
        text=text,
        method_name="init_host",
        call_line="self._run_performance_collector_on_init()",
        marker="# PLUGIN_INIT_PERFORMANCE_COLLECTOR",
    )

    text = _insert_call_before_last_return_in_create(
        text=text,
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