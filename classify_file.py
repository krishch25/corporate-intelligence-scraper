"""
EY Incubator – Classify uploaded Excel file
=============================================
Reads synthetic_training_large.xlsx (100 rows),
uses GPT-5.1 to add Material Group Desc., MTyp, M Class,
then writes a color-coded output Excel matching the VETRI taxonomy format.

Usage:
    python classify_file.py
"""

import json
import time
import pandas as pd
from llm_client import EYLLMClient

# ──────────────────────────────────────────────
#  Paths
# ──────────────────────────────────────────────
INPUT_FILE = "/Users/krishchoudhary/Downloads/excel-op 2/data/synthetic_training_large.xlsx"
OUTPUT_FILE = "/Users/krishchoudhary/Downloads/ey_incubator/classified_output.xlsx"

# ──────────────────────────────────────────────
#  LLM Classification Prompt
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are a senior procurement data analyst at CRI Pumps, a large industrial pump manufacturer.
You classify SAP material master data into a structured taxonomy.

For each input row, produce a JSON object with these fields:
- "material_group_desc": short material group name in UPPERCASE (e.g. "PAPER", "PAPER TUBE", "RING", "PUMP BOX", "SLEEVE", "FLANGE", "GREASE", "OIL", "CLEANING AGENT", "DIFFUSER", "BRACKET", "COUPLING", "WASHER", "IMPELLER", "PACKING BOX CART")
- "mtyp": SAP material type code:
    - "ZRAW" for Raw materials / Consumables
    - "HALB" for Subassembly / Semi-finished
    - "ZMCH" for Machined Material
- "m_class": material class code:
    - "ENGG" for engineering / mechanical items
    - "CHEM" for chemicals, lubricants, cleaning agents
    - "ELEC" for electrical items
    - "PACK" for packaging items
- "po_group": PO group number (use 114 for general raw materials, 101 for standard items, 105 for assemblies, 108 for electrical, 112 for machined parts)
- "plant_code": plant code (use 1010 for RANSAR II, 1000 for RANSAR I, 1070 for NARK, 1200 for GOFLEX – pick the most likely plant based on material type)
- "plant_desc": plant description matching the code

IMPORTANT RULES:
1. Return ONLY a valid JSON array. No markdown, no explanation, no code fences.
2. Each element corresponds to one input row, in the same order.
3. Derive classification from the material_description and material_type.
4. For Consumables (grease, oil, cleaning agents) → mtyp=ZRAW, m_class=CHEM
5. For Subassembly (P.BOX, pump boxes) → mtyp=HALB, m_class=ENGG
6. For Machined Material (flange, sleeve, coupling) → mtyp=ZMCH, m_class=ENGG"""


BATCH_SIZE = 25  # Process 25 rows at a time to stay within token limits


def classify_batch(client: EYLLMClient, batch: list[dict]) -> list[dict]:
    """Classify a batch of rows using GPT-5.1."""
    prompt = (
        "Classify each of the following material master rows.\n"
        "Return a JSON array with one object per row.\n\n"
        f"INPUT ROWS:\n{json.dumps(batch, indent=2)}"
    )

    response = client.chat(prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.1)

    if not response:
        raise RuntimeError("LLM returned no response.")

    # Clean response
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    return json.loads(cleaned)


def classify_all(df: pd.DataFrame) -> list[dict]:
    """Classify all rows in batches."""
    client = EYLLMClient()
    all_classifications = []

    # Build compact representation
    rows = []
    for _, row in df.iterrows():
        rows.append({
            "material_code": str(row["material_code"]),
            "material_type": str(row["material_type"]),
            "material_desc": str(row["material_description"]),
        })

    total_batches = (len(rows) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        print(f"    Batch {batch_num}/{total_batches} ({len(batch)} rows) ...")

        result = classify_batch(client, batch)
        all_classifications.extend(result)

        # Rate limiting: small delay between batches
        if i + BATCH_SIZE < len(rows):
            time.sleep(1)

    print(f"  ✅ Classified all {len(all_classifications)} rows")
    return all_classifications


def build_output(df: pd.DataFrame, classifications: list[dict]) -> pd.DataFrame:
    """Build the final output DataFrame."""
    out = pd.DataFrame()

    # Pareto placeholder (no spend data, assign based on material type)
    out["Pareto"] = df["material_type"].apply(
        lambda x: "P1" if x == "Subassembly" else ("P2" if x == "Machined Material" else "P3")
    )

    out["Material Code"] = df["material_code"]
    out["M Desc."] = df["material_description"]

    # LLM-classified fields
    out["Material Group Desc."] = [c["material_group_desc"] for c in classifications]
    out["MTyp"] = [c["mtyp"] for c in classifications]
    out["Material Type Desc."] = df["material_type"]
    out["M Class"] = [c["m_class"] for c in classifications]
    out["PO Group"] = [c["po_group"] for c in classifications]
    out["Plant Code"] = [c["plant_code"] for c in classifications]
    out["Plant Description"] = [c.get("plant_desc", "") for c in classifications]

    # Already-present classifications from input
    out["L0"] = df["l0"]
    out["L1"] = df["l1"]
    out["L2"] = df["l2"]

    return out


def write_colored_excel(df: pd.DataFrame, filename: str):
    """Write the output with color-coded headers matching the VETRI taxonomy image."""
    writer = pd.ExcelWriter(filename, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="Material Code Taxonomy", index=False, startrow=1, header=False)

    workbook = writer.book
    worksheet = writer.sheets["Material Code Taxonomy"]

    # ── Color scheme matching the VETRI screenshot ──
    # Dark blue headers for direct-mapped fields
    blue_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#4472C4", "font_color": "#FFFFFF", "text_wrap": True,
    })

    # Red/pink headers for LLM-classified fields (Material Group Desc.)
    red_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#FF0000", "font_color": "#FFFFFF", "text_wrap": True,
    })
    red_cell = workbook.add_format({"font_color": "#C00000"})

    # Green headers for SAP type codes (MTyp, M Class)
    green_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#00B050", "font_color": "#FFFFFF", "text_wrap": True,
    })
    green_cell = workbook.add_format({"font_color": "#006100"})

    # Orange headers for taxonomy (L0, L1, L2)
    orange_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#ED7D31", "font_color": "#FFFFFF", "text_wrap": True,
    })
    orange_cell = workbook.add_format({"font_color": "#BF8F00"})

    # Standard black header for other mapped fields
    black_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#D9E1F2", "font_color": "#000000", "text_wrap": True,
    })

    # Column → (header_format, data_format)
    col_formats = {
        "Pareto":               (blue_header,   None),
        "Material Code":        (blue_header,   None),
        "M Desc.":              (blue_header,   None),
        "Material Group Desc.": (red_header,    red_cell),
        "MTyp":                 (green_header,  green_cell),
        "Material Type Desc.":  (green_header,  green_cell),
        "M Class":              (green_header,  green_cell),
        "PO Group":             (black_header,  None),
        "Plant Code":           (black_header,  None),
        "Plant Description":    (black_header,  None),
        "L0":                   (orange_header, orange_cell),
        "L1":                   (orange_header, orange_cell),
        "L2":                   (orange_header, orange_cell),
    }

    col_widths = {
        "Pareto": 8, "Material Code": 16, "M Desc.": 45,
        "Material Group Desc.": 22, "MTyp": 8, "Material Type Desc.": 20,
        "M Class": 10, "PO Group": 10, "Plant Code": 12, "Plant Description": 24,
        "L0": 22, "L1": 22, "L2": 22,
    }

    # Write headers
    for col_num, col_name in enumerate(df.columns):
        hdr_fmt, _ = col_formats.get(col_name, (black_header, None))
        worksheet.write(0, col_num, col_name, hdr_fmt)
        worksheet.set_column(col_num, col_num, col_widths.get(col_name, 15))

    # Write data with cell formatting
    for row_idx in range(len(df)):
        for col_idx, col_name in enumerate(df.columns):
            _, data_fmt = col_formats.get(col_name, (None, None))
            val = df.iloc[row_idx, col_idx]
            if data_fmt:
                worksheet.write(row_idx + 1, col_idx, val, data_fmt)
            else:
                worksheet.write(row_idx + 1, col_idx, val)

    # Freeze top row + autofilter
    worksheet.freeze_panes(1, 0)
    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

    writer.close()
    print(f"\n✅ Saved color-coded Excel: {filename}")


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  EY Incubator – File Classifier (VETRI Taxonomy)")
    print("=" * 60)

    # 1. Read input
    print(f"\n[1/3] Reading input: {INPUT_FILE}")
    df_input = pd.read_excel(INPUT_FILE)
    print(f"  Loaded {len(df_input)} rows, {len(df_input.columns)} columns")

    # 2. Classify with LLM in batches
    print(f"\n[2/3] Classifying with GPT-5.1 (batch size = {BATCH_SIZE}) ...")
    classifications = classify_all(df_input)

    # 3. Build output and write Excel
    print(f"\n[3/3] Building output Excel ...")
    df_output = build_output(df_input, classifications)
    write_colored_excel(df_output, OUTPUT_FILE)

    print(f"\nDone! Open '{OUTPUT_FILE}' to review.")
