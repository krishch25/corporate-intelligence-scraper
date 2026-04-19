#!/usr/bin/env python3
"""
Generate 50,000+ rows of realistic procurement test data (input + expected output).
Based on real-world CRI Pumps / manufacturing procurement data patterns.
"""
import os
import random
import pandas as pd
from datetime import datetime, timedelta

# ─── CLASSIFICATION KNOWLEDGE BASE ───────────────────────────────────────────
# Each entry: (Material Type, Material Description pattern, Material Code, Material Group Desc,
#              MTyp, M Class, L0, L1, L2, L3, Direct/Indirect)

CLASSIFICATION_MAP = [
    # ═══ DIRECT RAW MATERIALS - COMMODITIES ═══
    # Copper
    ("Raw materials", "ROD COPPER EC GRADE 8mm ROUND", "286450", "ROD", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Copper", "Copper Rod", "Direct Spend"),
    ("Raw materials", "WIRE COPPER EC GRADE 2.5mm", "286451", "WIRE", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Copper", "Copper Wire", "Direct Spend"),
    ("Raw materials", "STRIP COPPER 0.5mm THICK", "286460", "STRIP", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Copper", "Copper Strip", "Direct Spend"),
    ("Raw materials", "TUBE COPPER 12mm OD", "286470", "TUBE", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Copper", "Copper Tube", "Direct Spend"),
    # Aluminium
    ("Raw materials", "INGOT ALUMINIUM LM6 GRADE", "287100", "INGOT", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Aluminium", "Aluminium Ingot", "Direct Spend"),
    ("Raw materials", "SHEET ALUMINIUM 1mm THICK", "287110", "SHEET", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Aluminium", "Aluminium Sheet", "Direct Spend"),
    ("Raw materials", "EXTRUSION ALUMINIUM PROFILE 40x40", "287120", "EXTRUSION", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Aluminium", "Aluminium Extrusion", "Direct Spend"),
    # Steel
    ("Raw materials", "PLATE STEEL MS 6mm THICK", "288200", "PLATE", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Steel", "Steel Plate", "Direct Spend"),
    ("Raw materials", "ROD STEEL SS304 12mm ROUND", "288210", "ROD", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Steel", "Steel Rod", "Direct Spend"),
    ("Raw materials", "SHEET STEEL CR 1.2mm", "288220", "SHEET", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Steel", "Steel Sheet", "Direct Spend"),
    ("Raw materials", "PIPE STEEL SS316 25NB SCH40", "288230", "PIPE", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Steel", "Steel Pipe", "Direct Spend"),
    ("Raw materials", "ANGLE STEEL MS 50x50x5", "288240", "ANGLE", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Steel", "Steel Angle", "Direct Spend"),
    # Cast Iron
    ("Raw materials", "CASTING CI GRADE FG260", "289300", "CASTING", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Cast Iron", "CI Casting", "Direct Spend"),
    ("Raw materials", "PIG IRON GRADE 2 FOUNDRY", "289310", "PIG IRON", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Cast Iron", "Pig Iron", "Direct Spend"),
    # Plastics & Polymers
    ("Raw materials", "GRANULES PPO NORYL 731 BLACK", "290400", "GRANULES", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Plastics & Polymers", "PPO Granules", "Direct Spend"),
    ("Raw materials", "GRANULES ABS NATURAL", "290410", "GRANULES", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Plastics & Polymers", "ABS Granules", "Direct Spend"),
    ("Raw materials", "RESIN EPOXY ARALDITE CY230", "290420", "RESIN", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Plastics & Polymers", "Epoxy Resin", "Direct Spend"),
    ("Raw materials", "SHEET PVC RIGID 3mm", "290430", "SHEET", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Plastics & Polymers", "PVC Sheet", "Direct Spend"),
    # Rubber
    ("Raw materials", "RUBBER NBR SHEET 3mm", "291500", "RUBBER", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Rubber", "NBR Rubber Sheet", "Direct Spend"),
    ("Raw materials", "O-RING VITON 25x3", "291510", "O-RING", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Rubber", "Viton O-Ring", "Direct Spend"),
    # Chemicals & Paints
    ("Raw materials", "PAINT EPOXY PRIMER RED OXIDE 20LTR", "292600", "PAINT", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Chemicals & Paints", "Epoxy Paint", "Direct Spend"),
    ("Raw materials", "VARNISH INSULATING CLASS F", "292610", "VARNISH", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Chemicals & Paints", "Insulating Varnish", "Direct Spend"),
    ("Raw materials", "ADHESIVE LOCTITE 243 50ML", "292620", "ADHESIVE", "ZRAW", "ENGG",
     "Direct Raw Material", "Commodities", "Chemicals & Paints", "Industrial Adhesive", "Direct Spend"),

    # ═══ DIRECT - FG/ASSEMBLIES ═══
    # Solar
    ("Raw materials", "SLRM 535WP SPV PX144 DCR CELLS", "275272", "SOLAR PANEL", "ZRAW", "ENGG",
     "FG/Assemblies", "FG/Assemblies", "Solar", "Solar Module", "Direct Spend"),
    ("Raw materials", "SOLAR INVERTER 5KW HYBRID", "275280", "SOLAR INVERTER", "ZRAW", "ENGG",
     "FG/Assemblies", "FG/Assemblies", "Solar", "Solar Inverter", "Direct Spend"),
    # Motors
    ("Subassembly", "MOTOR 3PH 5HP 1440RPM IE3 TEFC", "301100", "MOTOR", "ZHLB", "ENGG",
     "FG/Assemblies", "FG/Assemblies", "Motors & Drives", "Electric Motor", "Direct Spend"),
    ("Subassembly", "VFD 7.5KW 3PH 415V ABB ACS580", "301110", "VFD", "ZHLB", "ENGG",
     "FG/Assemblies", "FG/Assemblies", "Motors & Drives", "Variable Frequency Drive", "Direct Spend"),

    # ═══ DIRECT - MANUFACTURED COMPONENTS ═══
    # Machined Components
    ("Machined Material", "SLEE SS304 S4S-1-14m³", "WD040CS0031", "SLEEVE", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Machined Parts", "SS Sleeve", "Direct Spend"),
    ("Machined Material", "WASH CP 20.8 6.5 4 SS420 FN", "WD041CW0061", "WASHER", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Machined Parts", "SS Washer", "Direct Spend"),
    ("Machined Material", "SLEE 59 48 72 SS410", "184096", "SLEEVE", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Machined Parts", "SS Sleeve", "Direct Spend"),
    ("Machined Material", "IMPELLER SS316 4STG 150mm DIA", "185200", "IMPELLER", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Machined Parts", "SS Impeller", "Direct Spend"),
    ("Machined Material", "SHAFT SS410 25mm DIA 500L", "185210", "SHAFT", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Machined Parts", "SS Shaft", "Direct Spend"),
    ("Machined Material", "BUSH BRONZE 40ID 50OD 30L", "185220", "BUSH", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Machined Parts", "Bronze Bush", "Direct Spend"),
    ("Machined Material", "FLANGE SS304 150NB ASA150", "185230", "FLANGE", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Machined Parts", "SS Flange", "Direct Spend"),
    ("Machined Material", "COUPLING RIGID SS316 25mm", "185240", "COUPLING", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Machined Parts", "SS Coupling", "Direct Spend"),
    # Castings
    ("Machined Material", "CASING CI FG260 MACHINED 100MM", "186300", "CASING", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Castings", "CI Casing", "Direct Spend"),
    ("Machined Material", "BRACKET CI FG200 MOTOR MOUNT", "186310", "BRACKET", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Castings", "CI Bracket", "Direct Spend"),
    # Stampings & Pressings
    ("Machined Material", "COVER SS304 STAMPED 200mm DIA", "187400", "COVER", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Stampings & Pressings", "SS Cover", "Direct Spend"),
    ("Machined Material", "END BELL ALUMINIUM PRESSED", "187410", "END BELL", "ZHLB", "ENGG",
     "Direct Raw Material", "Manufactured Components", "Stampings & Pressings", "Aluminium End Bell", "Direct Spend"),

    # ═══ DIRECT - SUBASSEMBLIES ═══
    # Pump Parts
    ("Subassembly", "P.BOX 1.0HP CSCR DVAM ABS CRI 4\" M1", "232917", "PUMP BOX", "ZHLB", "ENGG",
     "Direct Raw Material", "Sub Assemblies", "Pump Components", "Pump Box Assembly", "Direct Spend"),
    ("Subassembly", "STATOR ASSY 1HP 4POLE CRI", "233100", "STATOR", "ZHLB", "ENGG",
     "Direct Raw Material", "Sub Assemblies", "Pump Components", "Stator Assembly", "Direct Spend"),
    ("Subassembly", "ROTOR ASSY 2HP 2POLE CRI", "233110", "ROTOR", "ZHLB", "ENGG",
     "Direct Raw Material", "Sub Assemblies", "Pump Components", "Rotor Assembly", "Direct Spend"),
    ("Subassembly", "CONTROL PANEL 3PH DOL STARTER", "233120", "PANEL", "ZHLB", "ENGG",
     "Direct Raw Material", "Sub Assemblies", "Electrical Components", "Control Panel", "Direct Spend"),
    # Plastic Components
    ("Subassembly", "BP.4\".DIFF ST CRI4R-2-N PPO 20% GF NATUR", "252086", "BASE PLATE", "ZHLB", "ENGG",
     "Direct Raw Material", "Sub Assemblies", "Plastic Moulded Parts", "PPO Base Plate", "Direct Spend"),
    ("Subassembly", "DFPL PPO-X/SS304 S4D-1F,2,5 85.8 33.3 ML", "WYM40DT0032", "DIFFUSER PLATE", "ZHLB", "ENGG",
     "Direct Raw Material", "Sub Assemblies", "Plastic Moulded Parts", "PPO Diffuser Plate", "Direct Spend"),
    ("Subassembly", "BRKT TOP PPO-X/NBR R31 37.5 FN", "101982", "BRACKET", "ZHLB", "ENGG",
     "Direct Raw Material", "Sub Assemblies", "Plastic Moulded Parts", "PPO Bracket", "Direct Spend"),
    ("Subassembly", "HOUSING ABS INJECTION MOULDED", "252100", "HOUSING", "ZHLB", "ENGG",
     "Direct Raw Material", "Sub Assemblies", "Plastic Moulded Parts", "ABS Housing", "Direct Spend"),

    # ═══ DIRECT - PACKAGING ═══
    ("Raw materials", "BOX CORRUGATED 5PLY 600x400x300", "310100", "BOX", "ZRAW", "ENGG",
     "Direct Raw Material", "Packaging", "Packaging", "Corrugated Box", "Direct Spend"),
    ("Raw materials", "PALLET WOOD FUMIGATED 1200x1000", "310110", "PALLET", "ZRAW", "ENGG",
     "Direct Raw Material", "Packaging", "Packaging", "Wood Pallet", "Direct Spend"),
    ("Raw materials", "WRAP STRETCH FILM 500mm 23MIC", "310120", "WRAP", "ZRAW", "ENGG",
     "Direct Raw Material", "Packaging", "Packaging", "Stretch Film", "Direct Spend"),
    ("Raw materials", "FOAM EPE SHEET 10mm 1x2M", "310130", "FOAM", "ZRAW", "ENGG",
     "Direct Raw Material", "Packaging", "Packaging", "EPE Foam", "Direct Spend"),

    # ═══ DIRECT - BOUGHT OUT ITEMS ═══
    # Bearings
    ("Raw materials", "BEARING 6205 2RS SKF", "320100", "BEARING", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Bearings & Seals", "Ball Bearing", "Direct Spend"),
    ("Raw materials", "SEAL MECH SS304/CARBON 25mm", "320110", "SEAL", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Bearings & Seals", "Mechanical Seal", "Direct Spend"),
    # Fasteners
    ("Raw materials", "BOLT HEX SS304 M10x40 FULL THREAD", "320200", "BOLT", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Fasteners", "SS Hex Bolt", "Direct Spend"),
    ("Raw materials", "NUT HEX SS304 M10", "320210", "NUT", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Fasteners", "SS Hex Nut", "Direct Spend"),
    ("Raw materials", "SCREW CSK SS304 M6x20", "320220", "SCREW", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Fasteners", "SS CSK Screw", "Direct Spend"),
    # Electrical Components
    ("Raw materials", "CAPACITOR 25MFD 440V RUN", "330100", "CAPACITOR", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Electrical Components", "Run Capacitor", "Direct Spend"),
    ("Raw materials", "CABLE SUBMERSIBLE 3C 2.5SQ PVC", "330110", "CABLE", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Electrical Components", "Submersible Cable", "Direct Spend"),
    ("Raw materials", "TERMINAL LUG TINNED 2.5SQ RING", "330120", "TERMINAL", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Electrical Components", "Terminal Lug", "Direct Spend"),
    ("Raw materials", "WINDING WIRE ENAMELLED SWG18", "330130", "WIRE", "ZRAW", "ENGG",
     "Direct Raw Material", "Bought Out Items", "Electrical Components", "Winding Wire", "Direct Spend"),

    # ═══ INDIRECT SPEND ═══
    # MRO - Maintenance Materials
    ("Raw materials", "GREASE LITHIUM MP3 15KG BUCKET", "400100", "GREASE", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Maintenance Materials", "Lubricant Grease", "Indirect Spend"),
    ("Raw materials", "OIL HYDRAULIC HLP68 20LTR", "400110", "OIL", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Maintenance Materials", "Hydraulic Oil", "Indirect Spend"),
    ("Raw materials", "BELT V A68 INDUSTRIAL", "400120", "BELT", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Maintenance Materials", "V-Belt", "Indirect Spend"),
    ("Raw materials", "FILTER ELEMENT HYDRAULIC 10MIC", "400130", "FILTER", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Maintenance Materials", "Hydraulic Filter", "Indirect Spend"),
    # Safety & PPE
    ("Raw materials", "GLOVES NITRILE DISPOSABLE L BOX100", "410100", "GLOVES", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Safety & PPE", "Safety Gloves", "Indirect Spend"),
    ("Raw materials", "HELMET SAFETY YELLOW ISI MARK", "410110", "HELMET", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Safety & PPE", "Safety Helmet", "Indirect Spend"),
    ("Raw materials", "GOGGLES SAFETY CLEAR POLYCARBONATE", "410120", "GOGGLES", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Safety & PPE", "Safety Goggles", "Indirect Spend"),
    ("Raw materials", "SHOES SAFETY STEEL TOE SIZE 8", "410130", "SHOES", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Safety & PPE", "Safety Shoes", "Indirect Spend"),
    # Tools & Consumables
    ("Raw materials", "WHEEL GRINDING 150x6x22 A24", "420100", "WHEEL", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Tools & Consumables", "Grinding Wheel", "Indirect Spend"),
    ("Raw materials", "ELECTRODE WELDING 3.15mm E6013 5KG", "420110", "ELECTRODE", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Tools & Consumables", "Welding Electrode", "Indirect Spend"),
    ("Raw materials", "DRILL BIT HSS 8mm STRAIGHT SHANK", "420120", "DRILL", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Tools & Consumables", "HSS Drill Bit", "Indirect Spend"),
    ("Raw materials", "BLADE HACKSAW BI-METAL 12\"", "420130", "BLADE", "ZRAW", "ENGG",
     "Indirect Spend", "MRO", "Tools & Consumables", "Hacksaw Blade", "Indirect Spend"),
    # Office & Admin
    ("Raw materials", "PAPER A4 75GSM REAM 500SHEETS", "500100", "PAPER", "ZRAW", "ENGG",
     "Indirect Spend", "Admin & Facilities", "Office Supplies", "A4 Paper", "Indirect Spend"),
    ("Raw materials", "TONER CARTRIDGE HP 26A BLACK", "500110", "TONER", "ZRAW", "ENGG",
     "Indirect Spend", "Admin & Facilities", "Office Supplies", "Printer Toner", "Indirect Spend"),
    # IT
    ("Raw materials", "LAPTOP DELL LATITUDE 5540 i5 16GB", "510100", "LAPTOP", "ZRAW", "ENGG",
     "Indirect Spend", "Admin & Facilities", "IT Equipment", "Laptop", "Indirect Spend"),
    ("Raw materials", "UPS 1KVA LINE INTERACTIVE APC", "510110", "UPS", "ZRAW", "ENGG",
     "Indirect Spend", "Admin & Facilities", "IT Equipment", "UPS System", "Indirect Spend"),
]

# ─── REFERENCE DATA ──────────────────────────────────────────────────────────

SUPPLIERS = [
    ("SILICONIX", "COIMBATORE", "33", "YES", "YES", "33AJUPS1829E1ZY"),
    ("SRI GANESH ENGINEERING WORKS", "COIMBATORE", "33", "YES", "NO", "33AOOPG7111A1ZJ"),
    ("GOLDPLAST ENTERPRISES", "COIMBATORE", "33", "YES", "NO", "33AHJPA3148D1ZY"),
    ("MOULDING TECHNOLOGIES", "COIMBATORE", "33", "YES", "NO", "33BKQMT7654R1ZP"),
    ("VEDANTA LIMITED", "JHARSUGUDA", "21", "NO", "NO", "21AABCV3459Q1Z4"),
    ("KUTCH COPPER LIMITED", "GANDHIDHAM", "24", "NO", "NO", "24AABCK5678L1ZN"),
    ("ALPEX SOLAR LIMITED", "NOIDA", "09", "NO", "NO", "09AALCA1234M1ZB"),
    ("TATA STEEL LIMITED", "JAMSHEDPUR", "20", "NO", "NO", "20AABCT5678P1Z8"),
    ("SKF INDIA LIMITED", "PUNE", "27", "NO", "NO", "27AABCS4567K1ZR"),
    ("BOSCH INDIA LIMITED", "BANGALORE", "29", "NO", "NO", "29AABCB3456J1ZL"),
    ("SIEMENS LIMITED", "MUMBAI", "27", "NO", "NO", "27AABCS9876D1ZF"),
    ("ABB INDIA LIMITED", "BANGALORE", "29", "NO", "NO", "29AABCA8765C1ZI"),
    ("SCHNEIDER ELECTRIC", "GURGAON", "06", "NO", "NO", "06AABCS5432B1ZO"),
    ("HINDALCO INDUSTRIES", "RENUKOOT", "09", "NO", "NO", "09AABCH6789A1ZT"),
    ("JSW STEEL LIMITED", "BELLARY", "29", "NO", "NO", "29AABCJ7890E1ZK"),
    ("3M INDIA LIMITED", "BANGALORE", "29", "NO", "NO", "29AABC37891F1ZU"),
    ("HAVELLS INDIA LIMITED", "NOIDA", "09", "NO", "NO", "09AABCH4567G1ZQ"),
    ("ESSVEE WIRES INDIA PVT LTD", "COIMBATORE", "33", "YES", "NO", "33AABCE5678H1ZP"),
    ("CG POWER AND IND SOLUTIONS", "MUMBAI", "27", "NO", "NO", "27AABCC6789I1ZN"),
    ("FINOLEX CABLES LIMITED", "PUNE", "27", "NO", "NO", "27AABCF7890J1ZM"),
]

PLANTS = [
    ("1000", "RANSAR INDUSTRIES-I", "1010", "RANSAR II"),
    ("1010", "RANSAR INDUSTRIES-II", "1010", "RANSAR II"),
    ("1070", "NARK INDUSTRIES", "1070", "NARK INDUSTRIES"),
    ("1200", "GOFLEX WIRE AND CABLES", "1200", "GOFLEX WIRE AND CABLES"),
    ("1605", "PUNE", "1605", "PUNE"),
    ("1628", "HISAR", "1628", "HISAR"),
    ("1300", "AHMEDABAD WORKS", "1300", "AHMEDABAD WORKS"),
    ("1400", "CHENNAI PLANT", "1400", "CHENNAI PLANT"),
]

PO_GROUPS = ["101", "105", "108", "112", "115", "120", "180"]


def generate_doc_number(prefix, length=10):
    return f"{prefix}{random.randint(10**(length-len(prefix)-1), 10**(length-len(prefix))-1)}"


def generate_date(start_year=2024, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.strftime("%d.%m.%Y")


def generate_test_data(num_rows=50000):
    print(f"Generating {num_rows} rows of test data...")

    input_rows = []
    output_rows = []

    for i in range(num_rows):
        if i % 10000 == 0 and i > 0:
            print(f"  Generated {i}/{num_rows} rows...")

        # Pick a random classification entry
        entry = random.choice(CLASSIFICATION_MAP)
        mat_type, mat_desc, mat_code, mat_grp_desc, mtyp, m_class, l0, l1, l2, l3, direct_indirect = entry

        # Pick random supplier, plant
        supplier = random.choice(SUPPLIERS)
        sup_name, city, state, msme, rpt, gst_code = supplier
        plant = random.choice(PLANTS)
        plnt_cd, plant_desc, prft_code, profit_centre = plant
        po_grp = random.choice(PO_GROUPS)

        # Generate quantities and prices
        qty = random.randint(1, 20000)
        unit_price = round(random.uniform(0.50, 15000.0), 2)
        inr_value = round(qty * unit_price, 2)
        
        # GST calculations
        gst_rate = random.choice([0.05, 0.12, 0.18, 0.28])
        is_igst = state != "33"  # Inter-state if not Tamil Nadu
        gst_value = round(inr_value * gst_rate, 2)
        cgst = 0 if is_igst else round(gst_value / 2, 2)
        sgst = 0 if is_igst else round(gst_value / 2, 2)
        igst = gst_value if is_igst else 0

        # Dates
        migo_date = generate_date()
        po_date = generate_date()
        miro_date = generate_date()
        sup_inv_date = generate_date()

        # Doc numbers
        migo_doc = generate_doc_number("500", 10)
        po_number = generate_doc_number("400", 10)
        miro_doc = generate_doc_number("510", 10)
        fi_doc = generate_doc_number("252", 10)
        sup_code = generate_doc_number("190", 7)
        sup_inv = f"INV/{random.randint(24,26)}-{random.randint(25,27)}/{random.randint(1000,9999)}"

        # Pareto classification
        pareto = "P1" if inr_value > 50000 else "P2"
        
        # For sorting (cumulative spend - simulate with random large number)
        for_sorting = round(inr_value * random.uniform(50, 500), 2)

        # ─── INPUT ROW ────────────────────────────────────────────
        input_row = {
            "Material Type": mat_type,
            "MIGO Doc": migo_doc,
            "MIGO DocDt": migo_date,
            "Reve. Doc": "",
            "PO Number": po_number,
            "PO Date": po_date,
            "PO Grp": po_grp,
            "Prft Code": prft_code,
            "Profit Centre Name": profit_centre,
            "Plnt Cd": plnt_cd,
            "Plant Description": plant_desc,
            "MIRO D.No": miro_doc,
            "MIRO D.Dt": miro_date,
            "FI DOC No": fi_doc,
            "Sup.": sup_code,
            "Supplier Name": sup_name,
            "City": city,
            "State": state,
            "MSME": msme,
            "RPT": rpt,
            "Material Code": mat_code,
            "Material Description": mat_desc,
            "UOM": "EA",
            "MIGO QTY": qty,
            "MIRO QTY": qty,
            "Unit Price": unit_price,
            "Curr": "INR",
            "Conv. Rt": 1,
            "D/C": "S",
            "Ln Cur": inr_value,
            "INR Line Value": inr_value,
            "InvReduVal": inr_value,
            "CGST Value": cgst,
            "SGST Value": sgst,
            "IGST Value": igst,
            "Others": 0,
            "Ass. Val.": inr_value,
            "GST/EXIM Code": gst_code,
            "Sup. Inv": sup_inv,
            "Sup. In.Dt": sup_inv_date,
        }

        # ─── OUTPUT ROW ───────────────────────────────────────────
        output_row = {
            "Pareto": pareto,
            "Material Code": mat_code,
            "M Desc.": mat_desc,
            "Material Group Desc.": mat_grp_desc,
            "MTyp": mtyp,
            "Material Type Desc.": mat_type,
            "M Class": m_class,
            "PO Group": po_grp,
            "Plant Code": plnt_cd,
            "Plant Description": plant_desc,
            "Supplier Name": sup_name,
            "Remark": "",
            "Direct/Indirect": direct_indirect,
            "L0": l0,
            "L1": l1,
            "L2": l2,
            "L3": l3,
            "Spend": inr_value,
            "For Sorting": for_sorting,
        }

        input_rows.append(input_row)
        output_rows.append(output_row)

    # Create DataFrames and save
    df_input = pd.DataFrame(input_rows)
    df_output = pd.DataFrame(output_rows)

    os.makedirs("data", exist_ok=True)
    
    input_path = "data/test_input_50k.xlsx"
    output_path = "data/expected_output_50k.xlsx"
    
    print(f"Saving input file ({len(df_input)} rows)...")
    df_input.to_excel(input_path, index=False, engine='openpyxl')
    print(f"  ✅ Saved to {input_path}")
    
    print(f"Saving expected output file ({len(df_output)} rows)...")
    df_output.to_excel(output_path, index=False, engine='openpyxl')
    print(f"  ✅ Saved to {output_path}")

    # Print classification distribution
    print(f"\n📊 Classification Summary:")
    print(f"  L0 unique: {df_output['L0'].nunique()} → {df_output['L0'].value_counts().to_dict()}")
    print(f"  L1 unique: {df_output['L1'].nunique()}")
    print(f"  L2 unique: {df_output['L2'].nunique()}")
    print(f"  L3 unique: {df_output['L3'].nunique()}")
    print(f"  Pareto: {df_output['Pareto'].value_counts().to_dict()}")
    
    return input_path, output_path


if __name__ == "__main__":
    generate_test_data(50000)
