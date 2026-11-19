import json
import re
from pathlib import Path


def clean_markdown_value(val: str) -> str:
    """Removes leading/trailing markdown bold markers, bullets, and extra whitespace."""
    val = val.strip()
    val = re.sub(r"^\*+\s*|\s*\*+$", "", val)
    return val.strip()


def extract_field(block: str, field_label: str) -> str:
    """
    Extracts a single '* **Field Label:** value' or '- **Field Label:** value' entry
    from a scheme block, even if the value spans multiple lines.
    """
    pattern = re.compile(
        rf"^\s*[-*]\s*\**{re.escape(field_label)}\s*:\**\s*(.+?)(?=\n\s*[-*]\s*\**[A-Za-z /]+:|\n##|\n---|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(block)
    if not match:
        return ""
    return clean_markdown_value(match.group(1))


def parse_markdown_schemes(md_path: str, json_output_path: str) -> None:
    text = Path(md_path).read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n")

    lines = text.split("\n")
    current_category = "General Welfare"
    scheme_chunks = []
    current_chunk_lines = []
    current_meta = None

    # Matches both '## SCHEME 1: Name' and '### SCHEME 1: Name'
    header_pattern = re.compile(r"^#{2,3}\s+SCHEME\s+(\d+)\s*:\s*(.+)$", re.IGNORECASE)
    category_pattern = re.compile(r"^##\s+(?!SCHEME\s+\d+)(.+)$", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()

        cat_match = category_pattern.match(stripped)
        if cat_match:
            if current_meta and current_chunk_lines:
                scheme_chunks.append((current_meta, "\n".join(current_chunk_lines)))
                current_meta = None
                current_chunk_lines = []
            current_category = cat_match.group(1).strip()
            continue

        sch_match = header_pattern.match(stripped)
        if sch_match:
            if current_meta and current_chunk_lines:
                scheme_chunks.append((current_meta, "\n".join(current_chunk_lines)))
            current_meta = {
                "scheme_number": int(sch_match.group(1)),
                "name": clean_markdown_value(sch_match.group(2)),
                "category": current_category,
            }
            current_chunk_lines = []
            continue

        if current_meta is not None:
            current_chunk_lines.append(line)

    if current_meta and current_chunk_lines:
        scheme_chunks.append((current_meta, "\n".join(current_chunk_lines)))

    schemes = []
    warnings = []

    for meta, block in scheme_chunks:
        num = meta["scheme_number"]
        state_central = extract_field(block, "State / Central")
        department = extract_field(block, "Department")
        benefits = extract_field(block, "Benefits")
        eligibility = extract_field(block, "Eligibility")
        docs_raw = extract_field(block, "Documents Required")
        how_to_apply = extract_field(block, "How to Apply")
        official_url = extract_field(block, "Official website link")
        myscheme_url = extract_field(block, "myScheme page link")
        date_collected = extract_field(block, "Date collected")

        documents = [d.strip() for d in docs_raw.split(",") if d.strip()]

        record = {
            "id": f"ap-scheme-{num}",
            "scheme_number": num,
            "category": meta["category"],
            "name": meta["name"],
            "state_or_central": state_central,
            "department": department,
            "benefits": benefits,
            "eligibility": eligibility,
            "documents_required": documents,
            "how_to_apply": how_to_apply,
            "official_website": official_url,
            "myscheme_link": myscheme_url,
            "date_collected": date_collected,
        }
        schemes.append(record)

        missing_fields = [k for k, v in record.items() if not v]
        if missing_fields:
            warnings.append(f"Scheme {num} ({meta['name']}) missing: {missing_fields}")

    schemes.sort(key=lambda x: x["scheme_number"])

    found_numbers = {s["scheme_number"] for s in schemes}
    expected_numbers = set(range(1, 191))
    missing_numbers = sorted(expected_numbers - found_numbers)

    Path(json_output_path).write_text(
        json.dumps(schemes, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Parsed {len(schemes)} / 190 schemes into '{json_output_path}'.")
    if missing_numbers:
        print(f"Missing scheme numbers: {missing_numbers}")
    else:
        print("Sequence check passed: All schemes 1 through 190 are present with 0 gaps.")

    if warnings:
        print("Field warnings:")
        for w in warnings:
            print("  -", w)
    else:
        print("Field check passed: Every single field across all 190 schemes is populated.")


if __name__ == "__main__":
    parse_markdown_schemes("ap_government_schemes_90.md", "schemes.json")
