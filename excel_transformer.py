"""
EY Incubator – Excel Data Transformer
======================================
Reads raw procurement input data (tab-separated),
uses GPT-5.1 to classify each row into the output schema
(Material Group, MTyp, L0-L3 hierarchy, Direct/Indirect, Pareto),
then writes a color-coded Excel file.

Usage:
    python excel_transformer.py
"""

import json
import io
import pandas as pd
from llm_client import EYLLMClient


# ──────────────────────────────────────────────
#  Sample Input Data (tab-separated)
# ──────────────────────────────────────────────
INPUT_TSV = """Material Type\tMIGO Doc\tMIGO DocDt\tReve. Doc\tPO Number\tPO Date\tPO Grp\tPrft Code\tProfit Centre Name\tPlnt Cd\tPlant Description\tMIRO D.No\tMIRO D.Dt\tFI DOC No\tSup.\tSupplier Name\tCity\tState\tMSME\tRPT\tMaterial Code\tMaterial Description\tUOM\tMIGO QTY\tMIRO QTY\tUnit Price\tCurr\tConv. Rt\tD/C\tLn Cur\tINR Line Value\tInvReduVal\tCGST Value\tSGST Value\tIGST Value\tOthers\tAss. Val.\tGST/EXIM Code\tSup. Inv\tSup. In.Dt
Subassembly\t5001493017\t18.06.2025\t\t4000280847\t26.05.2025\t108\t1010\tRANSAR II\t1010\tRANSAR INDUSTRIES-II\t5105882242\t20.06.2025\t2520035635\t1900433\tSILICONIX\tCOIMBATORE\t33\tYES\tYES\t232917\tP.BOX 1.0HP CSCR DVAM ABS CRI 4" M1\tEA\t100\t99\t1237.00\tINR\t1\tS\t122463.00\t122463.00\t0\t11133.00\t11133.00\t0\t0\t122463.00\t33AJUPS1829E1ZY\tTI/25-26/0060\t18.06.2025
Machined Material\t5001495668\t19.06.2025\t\t4000266824\t16.04.2025\t112\t1070\tNARK INDUSTRIES\t1070\tNARK INDUSTRIES\t5105882243\t20.06.2025\t2520035636\t1900306\tSRI GANESH ENGINEERING WORKS\tCOIMBATORE\t33\tYES\tNO\tWD040CS0031\tSLEE SS304 S4S-1-14m³\tEA\t1000.00\t1000.00\t61.51\tINR\t1\tS\t61510.00\t61510.00\t0\t5535.90\t5535.90\t0\t0\t61510.00\t33AOOPG7111A1ZJ\tSGE/0235/25-26\t19.06.2025
Raw materials\t5001495668\t19.06.2025\t\t4000274465\t08.05.2025\t112\t1070\tNARK INDUSTRIES\t1070\tNARK INDUSTRIES\t5105882243\t20.06.2025\t2520035636\t1900306\tSRI GANESH ENGINEERING WORKS\tCOIMBATORE\t33\tYES\tNO\t104800\tCOUP SS329 S8C 42.03D 22.1D 43.5\tEA\t300\t300\t221.04\tINR\t1\tS\t66312.00\t66312.00\t0\t5968.08\t5968.08\t0\t0\t66312.00\t33AOOPG7111A1ZJ\tSGE/0235/25-26\t19.06.2025
Machined Material\t5001495668\t19.06.2025\t\t4000279116\t21.05.2025\t112\t1070\tNARK INDUSTRIES\t1070\tNARK INDUSTRIES\t5105882243\t20.06.2025\t2520035636\t1900306\tSRI GANESH ENGINEERING WORKS\tCOIMBATORE\t33\tYES\tNO\tWD041CW0061\tWASH CP 20.8 6.5 4 SS420 FN\tEA\t7\t7\t10.85\tINR\t1\tS\t75.95\t75.95\t0\t6.84\t6.84\t0\t0\t75.95\t33AOOPG7111A1ZJ\tSGE/0235/25-26\t19.06.2025
Machined Material\t5001495668\t19.06.2025\t\t4000279117\t21.05.2025\t112\t1070\tNARK INDUSTRIES\t1070\tNARK INDUSTRIES\t5105882243\t20.06.2025\t2520035636\t1900306\tSRI GANESH ENGINEERING WORKS\tCOIMBATORE\t33\tYES\tNO\tWD041CW0061\tWASH CP 20.8 6.5 4 SS420 FN\tEA\t2000.00\t2000.00\t10.85\tINR\t1\tS\t21700.00\t21700.00\t0\t1953.00\t1953.00\t0\t0\t21700.00\t33AOOPG7111A1ZJ\tSGE/0235/25-26\t19.06.2025
Machined Material\t5001495668\t19.06.2025\t\t4000279119\t21.05.2025\t112\t1070\tNARK INDUSTRIES\t1070\tNARK INDUSTRIES\t5105882243\t20.06.2025\t2520035636\t1900306\tSRI GANESH ENGINEERING WORKS\tCOIMBATORE\t33\tYES\tNO\tWD041CW0061\tWASH CP 20.8 6.5 4 SS420 FN\tEA\t139\t139\t10.85\tINR\t1\tS\t1508.15\t1508.15\t0\t135.73\t135.73\t0\t0\t1508.15\t33AOOPG7111A1ZJ\tSGE/0235/25-26\t19.06.2025
Machined Material\t5001495668\t19.06.2025\t\t4400070966\t19.06.2025\t112\t1070\tNARK INDUSTRIES\t1070\tNARK INDUSTRIES\t5105882243\t20.06.2025\t2520035636\t1900306\tSRI GANESH ENGINEERING WORKS\tCOIMBATORE\t33\tYES\tNO\t184096\tSLEE 59 48 72 SS410\tEA\t10\t10\t178.4\tINR\t1\tS\t1784.00\t1784.00\t0\t160.56\t160.56\t0\t0\t1784.00\t33AOOPG7111A1ZJ\tSGE/0235/25-26\t19.06.2025
Subassembly\t5001492295\t18.06.2025\t\t4000265946\t12.04.2025\t105\t1010\tRANSAR II\t1010\tRANSAR INDUSTRIES-II\t5105882245\t20.06.2025\t2520035638\t1900118\tGOLDPLAST ENTERPRISES\tCOIMBATORE\t33\tYES\tNO\t252086\tBP.4".DIFF ST CRI4R-2-N PPO 20% GF NATUR\tEA\t5000.00\t5000.00\t14.23\tINR\t1\tS\t71150.00\t71150.00\t0\t6403.50\t6403.50\t0\t0\t71150.00\t33AHJPA3148D1ZY\t70/25-26\t18.06.2025
Machined Material\t5001492295\t18.06.2025\t\t4000287362\t16.06.2025\t105\t1010\tRANSAR II\t1010\tRANSAR INDUSTRIES-II\t5105882245\t20.06.2025\t2520035638\t1900118\tGOLDPLAST ENTERPRISES\tCOIMBATORE\t33\tYES\tNO\tWYM40DT0032\tDFPL PPO-X/SS304 S4D-1F,2,5 85.8 33.3 ML\tEA\t18000.00\t18000.00\t8.87\tINR\t1\tS\t159660.00\t159660.00\t0\t14369.40\t14369.40\t0\t0\t159660.00\t33AHJPA3148D1ZY\t70/25-26\t18.06.2025
Subassembly\t5001491884\t18.06.2025\t\t4000250174\t24.02.2025\t105\t1010\tRANSAR II\t1010\tRANSAR INDUSTRIES-II\t5105882246\t20.06.2025\t2520035639\t1900310\tMOULDING TECHNOLOGIES\tCOIMBATORE\t33\tYES\tNO\t101982\tBRKT TOP PPO-X/NBR R31 37.5 FN\tEA\t100\t100\t41.78\tINR\t1\tS\t4178.00\t4178.00\t0\t376.02\t376.02\t0\t0\t4178.00\t33AHJPA3148D1ZY\t70/25-26\t18.06.2025"""


# ──────────────────────────────────────────────
#  LLM Classification Prompt
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """You are a senior procurement data analyst at a large manufacturing company (CRI Pumps / similar).
You classify raw SAP procurement line items into a structured spend taxonomy.

Your task: For each input row, produce a JSON object with these fields:
- "material_group_desc": short material group name (e.g., "SLEEVE", "COUPLING", "WASHER", "BRACKET", "PUMP BOX", "DIFFUSER", "ROD")
- "mtyp": SAP material type code. Use these exact codes:
    - "ZRAW" for Raw materials
    - "HALB" for Subassembly / Semi-finished
    - "ZMCH" for Machined Material
- "m_class": material class, e.g., "ENGG" for engineering items, "ELEC" for electrical, "PACK" for packaging
- "direct_indirect": "Direct Spend" if the material is used directly in manufacturing/production, "Indirect" otherwise
- "L0": top-level spend category. Examples: "Direct Raw Material", "FG/Assemblies", "Bought-Out Parts"
- "L1": second level. Examples: "Commodities", "Machined Components", "Moulded Parts", "Bought-Out Items"
- "L2": third level - the commodity/product category. Examples: "Stainless Steel", "Plastics", "Copper", "Electrical"
- "L3": fourth level - the specific product family. Examples: "SS Sleeve", "SS Coupling", "PPO Bracket", "Pump Box Assembly"
- "remark": any relevant observation (leave empty string if none)

IMPORTANT RULES:
1. Return ONLY a valid JSON array. No markdown, no explanation, no code fences.
2. Each element in the array corresponds to one input row, in the same order.
3. Derive classification from the Material Description, Material Type, and Material Code.
4. For machined materials with SS (stainless steel) codes, classify under Stainless Steel.
5. For PPO/plastic materials, classify under Plastics.
6. For electrical/motor items, classify under Electrical."""


def classify_with_llm(df: pd.DataFrame) -> list[dict]:
    """Send the input rows to GPT-5.1 and get classification back as JSON."""
    client = EYLLMClient()

    # Build a compact representation of each row for the LLM
    rows_for_llm = []
    for _, row in df.iterrows():
        rows_for_llm.append({
            "material_type": row["Material Type"],
            "material_code": str(row["Material Code"]),
            "material_desc": row["Material Description"],
            "unit_price": row["Unit Price"],
            "supplier": row["Supplier Name"],
        })

    prompt = (
        "Classify each of the following procurement line items.\n"
        "Return a JSON array with one object per row.\n\n"
        f"INPUT ROWS:\n{json.dumps(rows_for_llm, indent=2)}"
    )

    print(f"  Sending {len(rows_for_llm)} rows to GPT-5.1 for classification ...")
    response = client.chat(prompt=prompt, system_prompt=SYSTEM_PROMPT, temperature=0.2)

    if not response:
        raise RuntimeError("LLM returned no response. Check API connectivity.")

    # Parse JSON from the response
    # Strip any accidental markdown fences
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    classifications = json.loads(cleaned)
    print(f"  ✅ Received {len(classifications)} classifications from GPT-5.1")
    return classifications


def build_output_df(df_input: pd.DataFrame, classifications: list[dict]) -> pd.DataFrame:
    """Combine input data with LLM classifications into the output schema."""

    # Ensure numeric for Ass. Val.
    df_input["Ass. Val."] = pd.to_numeric(
        df_input["Ass. Val."].astype(str).str.replace(",", ""), errors="coerce"
    ).fillna(0)

    out = pd.DataFrame()

    # Direct mappings from input
    out["Material Code"] = df_input["Material Code"]
    out["Material Description"] = df_input["Material Description"]

    # LLM-classified fields
    out["Material Group Desc."] = [c["material_group_desc"] for c in classifications]
    out["MTyp"]                 = [c["mtyp"] for c in classifications]
    out["Material Type Desc."]  = df_input["Material Type"]
    out["M Class"]              = [c["m_class"] for c in classifications]
    out["PO Group"]             = df_input["PO Grp"]
    out["Plant Code"]           = df_input["Plnt Cd"]
    out["Plant Description"]    = df_input["Plant Description"]
    out["Supplier Name"]        = df_input["Supplier Name"]
    out["Remark"]               = [c.get("remark", "") for c in classifications]
    out["Direct/Indirect"]      = [c["direct_indirect"] for c in classifications]
    out["L0"]                   = [c["L0"] for c in classifications]
    out["L1"]                   = [c["L1"] for c in classifications]
    out["L2"]                   = [c["L2"] for c in classifications]
    out["L3"]                   = [c["L3"] for c in classifications]

    # Financial aggregation
    out["Spend"] = df_input.groupby("Material Code")["Ass. Val."].transform("sum")

    # For Sorting = total spend across all suppliers/plants for each material
    mat_total = df_input.groupby("Material Code")["Ass. Val."].sum()
    out["For Sorting"] = out["Material Code"].map(mat_total)

    # Pareto classification (P1 = top 80%, P2 = next 15%, P3 = rest)
    total_spend = out["For Sorting"].sum()
    sorted_spend = out.drop_duplicates("Material Code").sort_values("For Sorting", ascending=False)
    cumulative = sorted_spend["For Sorting"].cumsum() / total_spend
    pareto_map = {}
    for mc, cum_pct in zip(sorted_spend["Material Code"], cumulative):
        if cum_pct <= 0.80:
            pareto_map[mc] = "P1"
        elif cum_pct <= 0.95:
            pareto_map[mc] = "P2"
        else:
            pareto_map[mc] = "P3"
    out["Pareto"] = out["Material Code"].map(pareto_map)

    # Reorder columns to match the desired output
    cols = [
        "Pareto", "Material Code", "Material Description", "Material Group Desc.",
        "MTyp", "Material Type Desc.", "M Class", "PO Group", "Plant Code",
        "Plant Description", "Supplier Name", "Remark", "Direct/Indirect",
        "L0", "L1", "L2", "L3", "Spend", "For Sorting",
    ]
    return out[cols]


def write_colored_excel(df: pd.DataFrame, filename: str = "categorized_output.xlsx"):
    """Write the output DataFrame to a color-coded Excel file."""
    writer = pd.ExcelWriter(filename, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="Categorized Data", index=False, startrow=1, header=False)

    workbook = writer.book
    worksheet = writer.sheets["Categorized Data"]

    # ── Color Scheme (matching the user's image) ──────────────
    # Section 1: Black headers (direct mapping fields)
    black_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#D9E1F2", "font_color": "#000000", "text_wrap": True,
    })
    # Section 2: Red headers & text (classification fields added by LLM)
    red_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#FFC7CE", "font_color": "#9C0006", "text_wrap": True,
    })
    red_cell = workbook.add_format({"font_color": "#9C0006"})

    # Section 3: Green headers & text (SAP type code)
    green_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#C6EFCE", "font_color": "#006100", "text_wrap": True,
    })
    green_cell = workbook.add_format({"font_color": "#006100"})

    # Section 4: Orange headers (L1, L2, L3 taxonomy)
    orange_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#FCE4D6", "font_color": "#BF8F00", "text_wrap": True,
    })
    orange_cell = workbook.add_format({"font_color": "#BF8F00"})

    # Section 5: Purple headers (spend / financial)
    purple_header = workbook.add_format({
        "bold": True, "border": 1, "align": "center", "valign": "vcenter",
        "bg_color": "#E2D0F8", "font_color": "#7030A0", "text_wrap": True,
    })
    money_fmt = workbook.add_format({"num_format": "#,##0", "font_color": "#7030A0"})

    # Map each column to its header format and data format
    col_formats = {
        "Pareto":               (black_header, None),
        "Material Code":        (black_header, None),
        "Material Description": (black_header, None),
        "Material Group Desc.": (red_header,   red_cell),
        "MTyp":                 (green_header, green_cell),
        "Material Type Desc.":  (red_header,   red_cell),
        "M Class":              (green_header, green_cell),
        "PO Group":             (black_header, None),
        "Plant Code":           (black_header, None),
        "Plant Description":    (black_header, None),
        "Supplier Name":        (black_header, None),
        "Remark":               (red_header,   red_cell),
        "Direct/Indirect":      (red_header,   red_cell),
        "L0":                   (orange_header, orange_cell),
        "L1":                   (orange_header, orange_cell),
        "L2":                   (orange_header, orange_cell),
        "L3":                   (orange_header, orange_cell),
        "Spend":                (purple_header, money_fmt),
        "For Sorting":          (purple_header, money_fmt),
    }

    # Column widths
    col_widths = {
        "Pareto": 8, "Material Code": 18, "Material Description": 40,
        "Material Group Desc.": 20, "MTyp": 8, "Material Type Desc.": 18,
        "M Class": 10, "PO Group": 10, "Plant Code": 10, "Plant Description": 22,
        "Supplier Name": 28, "Remark": 15, "Direct/Indirect": 15,
        "L0": 20, "L1": 18, "L2": 16, "L3": 20, "Spend": 18, "For Sorting": 18,
    }

    # Write headers
    for col_num, col_name in enumerate(df.columns):
        hdr_fmt, _ = col_formats.get(col_name, (black_header, None))
        worksheet.write(0, col_num, col_name, hdr_fmt)
        worksheet.set_column(col_num, col_num, col_widths.get(col_name, 15))

    # Write data with cell-level formatting
    for row_idx in range(len(df)):
        for col_idx, col_name in enumerate(df.columns):
            _, data_fmt = col_formats.get(col_name, (None, None))
            val = df.iloc[row_idx, col_idx]
            if data_fmt:
                worksheet.write(row_idx + 1, col_idx, val, data_fmt)
            else:
                worksheet.write(row_idx + 1, col_idx, val)

    # Freeze top row
    worksheet.freeze_panes(1, 0)

    writer.close()
    print(f"\n✅ Generated color-coded Excel: {filename}")


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  EY Incubator – Excel Data Transformer")
    print("=" * 60)

    # 1. Parse input
    print("\n[1/3] Reading input data ...")
    df_input = pd.read_csv(io.StringIO(INPUT_TSV), sep="\t")
    print(f"  Loaded {len(df_input)} rows, {len(df_input.columns)} columns")

    # 2. Classify with LLM
    print("\n[2/3] Classifying with GPT-5.1 ...")
    classifications = classify_with_llm(df_input)

    # 3. Build & write output
    print("\n[3/3] Building output Excel ...")
    df_output = build_output_df(df_input, classifications)
    write_colored_excel(df_output)

    print("\nDone! Open 'categorized_output.xlsx' to review.")
