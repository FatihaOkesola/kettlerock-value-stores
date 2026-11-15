"""One-off authoring script for the product master (config/structure/products_master.csv).

The product master is authored structure: about 180 items on eight fixed price points
across three categories (specification section 6). Item-level variation is
deterministic (no random draws), so identifiers and attributes never change between
regenerations. Department averages are taken from calibrated_parameters.csv, and the
tests check the frozen file against them.
"""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "config" / "structure" / "products_master.csv"
CAL = ROOT.parent / "01_calibration" / "calibrated_parameters.csv"

PARAMS = {r["parameter_id"]: r for r in csv.DictReader(open(CAL, encoding="utf-8"))}
MARGIN = {"Consumables": float(PARAMS["MP-05"]["central_value"]) / 100,
          "General merchandise": float(PARAMS["MP-06"]["central_value"]) / 100,
          "Seasonal": float(PARAMS["MP-07"]["central_value"]) / 100}
FREIGHT = float(PARAMS["MP-14"]["central_value"]) / 100
DUTY = float(PARAMS["MP-15"]["central_value"]) / 100
BASE_FX = 1.3501   # USD/CAD monthly average, February 2024 (GOV-BOC-FX): first month of FY2025

# department -> (category, seasonal window, import share of items, duty multiplier, price points, item names)
DEPARTMENTS = {
    "Snacks and confectionery": ("Consumables", "", 0.0, 0.5, [1.25, 1.50, 2.00, 2.50, 3.00], [
        "Potato chips", "Tortilla chips", "Pretzels", "Popcorn", "Gummy bears", "Sour candy strips",
        "Chocolate bar", "Mint tin", "Cookies", "Wafer bars", "Granola bars", "Trail mix",
        "Peanuts", "Crackers", "Fruit snacks", "Licorice", "Lollipops", "Bubble gum",
        "Rice cakes", "Cheese puffs", "Jelly beans", "Hard candy bag", "Biscuit pack", "Seaweed snack"]),
    "Cleaning and paper": ("Consumables", "", 0.0, 0.5, [1.25, 1.50, 2.00, 2.50, 3.00, 4.00], [
        "Paper towels", "Bathroom tissue", "Facial tissue", "Paper plates", "Napkins", "Garbage bags",
        "Dish soap", "Sponges", "All-purpose cleaner", "Glass cleaner", "Bleach", "Laundry detergent",
        "Dryer sheets", "Toilet bowl cleaner", "Scrub brush", "Rubber gloves", "Aluminium foil",
        "Plastic wrap", "Freezer bags", "Sandwich bags", "Microfibre cloths", "Air freshener",
        "Disinfecting wipes", "Mop refill"]),
    "Personal care": ("Consumables", "", 0.5, 0.8, [1.25, 1.50, 2.00, 2.50, 3.00, 4.00], [
        "Toothpaste", "Toothbrush twin pack", "Shampoo", "Conditioner", "Body wash", "Bar soap",
        "Hand soap", "Deodorant", "Cotton swabs", "Cotton pads", "Hair ties", "Hair brush",
        "Nail file set", "Lip balm", "Hand cream", "Bandages", "Razors", "Shaving cream",
        "Mouthwash", "Dental floss", "Comb set", "Makeup sponges", "Travel bottles", "Face masks"]),
    "Kitchen and home": ("General merchandise", "", 0.7, 1.0, [1.50, 2.00, 2.50, 3.00, 4.00, 5.00, 6.00], [
        "Storage containers", "Kitchen utensils set", "Measuring cups", "Mixing bowl", "Cutting board",
        "Dish towels", "Oven mitt", "Baking pan", "Food storage jars", "Coat hangers", "Storage bins",
        "Picture frame", "Candles", "Batteries", "Light bulbs", "Extension cord", "Phone charger cable",
        "Drinking glasses", "Mugs", "Plastic cutlery", "Water bottle", "Laundry basket"]),
    "Party and stationery": ("General merchandise", "", 0.75, 1.0, [1.25, 1.50, 2.00, 2.50, 3.00, 4.00, 5.00], [
        "Balloons", "Gift bags", "Wrapping paper", "Greeting cards", "Party hats", "Streamers",
        "Birthday candles", "Tablecloth", "Pens", "Pencils", "Notebooks", "Sticky notes",
        "Markers", "Tape", "Scissors", "Glue sticks", "Envelopes", "File folders",
        "Highlighters", "Erasers", "Gift tissue paper", "Party favours"]),
    "Toys and crafts": ("General merchandise", "", 0.85, 1.6, [1.50, 2.00, 3.00, 4.00, 5.00, 6.00], [
        "Colouring book", "Crayons", "Play dough", "Bubbles", "Toy cars", "Puzzle",
        "Craft paint", "Paint brushes", "Craft foam", "Pipe cleaners", "Stickers", "Bouncy ball",
        "Card game", "Plush toy", "Water gun", "Kite", "Beads kit", "Slime kit",
        "Building blocks", "Chalk", "Yo-yo", "Action figure"]),
    "Halloween": ("Seasonal", "Halloween", 0.9, 1.6, [1.25, 2.00, 3.00, 4.00, 5.00, 6.00], [
        "Halloween candy bag", "Costume mask", "Treat bags", "Pumpkin carving kit", "Fake cobwebs",
        "Halloween lights", "Face paint", "Witch hat", "Glow sticks", "Halloween decor sign"]),
    "Christmas": ("Seasonal", "Christmas", 0.9, 1.6, [1.25, 2.00, 3.00, 4.00, 5.00, 6.00], [
        "Christmas lights", "Ornament set", "Tinsel", "Stocking", "Christmas gift wrap", "Gift tags",
        "Advent calendar", "Christmas candy cane", "Tree topper", "Holiday mugs", "Christmas cards",
        "Santa hat", "Holiday baking tins", "Christmas wreath"]),
    "Easter and spring": ("Seasonal", "Easter and spring", 0.9, 1.6, [1.25, 2.00, 3.00, 4.00, 5.00], [
        "Easter eggs", "Easter basket", "Chocolate bunny", "Egg dye kit", "Easter grass", "Spring garden gloves"]),
    "Summer": ("Seasonal", "Summer", 0.9, 1.6, [1.25, 2.00, 3.00, 4.00, 5.00, 6.00], [
        "Sunglasses", "Beach ball", "Pool noodle", "Sand toys", "Picnic plates", "Bug spray"]),
    "Back-to-school": ("Seasonal", "Back-to-school", 0.85, 1.0, [1.25, 2.00, 3.00, 4.00, 5.00], [
        "Backpack", "Lunch bag", "Pencil case", "Binder", "Geometry set", "School supplies bundle"]),
}


def spread(n, width):
    """Deterministic, zero-mean offsets for n items: evenly spaced in [-width, +width]."""
    if n == 1:
        return [0.0]
    return [-width + 2 * width * i / (n - 1) for i in range(n)]


def main():
    rows, pid = [], 0
    for dept, (cat, window, import_share, duty_mult, points, names) in DEPARTMENTS.items():
        n = len(names)
        margin_offsets = spread(n, 0.03)                     # item margins vary +/-3 points around the category
        margin_offsets = margin_offsets[::2] + margin_offsets[1::2]   # de-correlate from price point order
        n_import = round(n * import_share)
        for i, name in enumerate(names):
            pid += 1
            price = points[i % len(points)]
            margin = MARGIN[cat] + margin_offsets[i]
            landed_cad = round(price * (1 - margin), 4)
            imported = i < n_import
            freight = FREIGHT if imported else 0.0
            duty = round(DUTY * duty_mult, 4) if imported else 0.0
            if imported:
                supplier_cost = round(landed_cad / (1 + freight + duty) / BASE_FX, 4)
                currency = "USD"
            else:
                supplier_cost = landed_cad
                currency = "CAD"
            rows.append({
                "product_id": f"P{pid:03d}", "product_name": name, "category": cat, "department": dept,
                "price_point": f"{price:.2f}", "import_flag": int(imported), "supplier_currency": currency,
                "base_supplier_cost": f"{supplier_cost:.4f}", "inbound_freight_rate": f"{freight:.4f}",
                "duty_tariff_rate": f"{duty:.4f}", "base_landed_cost_cad": f"{landed_cad:.4f}",
                "product_margin_at_ticket": f"{margin:.4f}", "seasonal_window": window,
                "launch_date": "2024-02-04", "discontinue_date": "",
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} products written to {OUT}")


if __name__ == "__main__":
    main()
