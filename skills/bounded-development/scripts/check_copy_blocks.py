"""Check copyable output structure; not wording quality, UI buttons or live actions."""
import argparse
import json
import re
from pathlib import Path

ALLOWED = {"copy_block_count", "required_same_block", "first_block_suffix",
           "forbidden_in_blocks"}

def blocks(text):
    patterns = [
        r"(?ms)^\x60{3}(?:text|markdown)?[ \t]*\n(.*?)^\x60{3}[ \t]*(?=\n|$)",
        r"(?ms)^:::writing\{[^\n]*\}[ \t]*\n(.*?)^:::[ \t]*(?=\n|$)",
    ]
    found = []
    normalized = text.replace("\r\n", "\n")
    for pattern in patterns:
        for match in re.finditer(pattern, normalized):
            found.append((match.start(), match.group(1).strip()))
    return [value for _, value in sorted(found)]

def check(text, contract):
    if not isinstance(contract, dict) or not contract or set(contract) - ALLOWED:
        raise ValueError("unsupported or invalid contract")
    count = contract.get("copy_block_count")
    if count is not None and (type(count) is not int or count < 0):
        raise ValueError("copy_block_count must be a nonnegative integer")
    groups = contract.get("required_same_block", [])
    forbidden = contract.get("forbidden_in_blocks", [])
    suffix = contract.get("first_block_suffix")
    if not isinstance(groups, list) or any(
        not isinstance(g, list) or not g or
        any(not isinstance(x, str) or not x for x in g) for g in groups
    ):
        raise ValueError("required_same_block must contain nonempty string groups")
    if not isinstance(forbidden, list) or any(
        not isinstance(x, str) or not x for x in forbidden
    ):
        raise ValueError("forbidden_in_blocks must contain nonempty strings")
    if suffix is not None and (not isinstance(suffix, str) or not suffix):
        raise ValueError("first_block_suffix must be a nonempty string")
    output = blocks(text)
    errors = []
    if count is not None and len(output) != count:
        errors.append("copy_block_count")
    for i, group in enumerate(groups):
        if not any(all(x in b for x in group) for b in output):
            errors.append("required_same_block:" + str(i))
    if suffix is not None and (
        not output or not output[0].endswith(suffix.replace("\r\n", "\n").strip())
    ):
        errors.append("first_block_suffix")
    for value in forbidden:
        if any(value in b for b in output):
            errors.append("forbidden_in_blocks:" + value)
    return {"status": "passed" if not errors else "failed",
            "copy_blocks": len(output), "errors": errors,
            "scope": "output_structure_only"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--contract", required=True)
    args = parser.parse_args()
    contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
    result = check(Path(args.artifact).read_text(encoding="utf-8"), contract)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())
