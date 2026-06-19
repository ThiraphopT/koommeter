#!/usr/bin/env python3
"""
KoomMeter — CSV to products.json converter
==========================================
คอลัมน์ CSV:
  id, cat, sub, brand, name, img, price, old,
  s_price, s_perf, s_durability, s_reviews,
  rating, reviews, badge, pros, cons,
  link_shopee, link_lazada, link_amazon

pros/cons ใส่หลายรายการโดยคั่นด้วย | เช่น  ราคาถูก|ใช้ง่าย
score คำนวณอัตโนมัติตามสูตร: 0.35*s_price + 0.25*s_perf + 0.20*s_durability + 0.20*s_reviews

การใช้งาน:
  python convert.py products.csv           # แปลงเป็น products.json
  python convert.py products.csv --verify  # ตรวจสอบ score ใน CSV ว่าตรงสูตรหรือไม่
"""

import csv
import json
import sys
import argparse
from pathlib import Path


def calc_score(s_price, s_perf, s_durability, s_reviews):
    """คำนวณคะแนนรวมตามสูตร KoomMeter"""
    return round(0.35 * s_price + 0.25 * s_perf + 0.20 * s_durability + 0.20 * s_reviews)


def convert(csv_path: str, out_path: str = "products.json", verify: bool = False):
    products = []
    errors = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # row 1 = header
            try:
                s = {
                    "price":      int(row["s_price"]),
                    "perf":       int(row["s_perf"]),
                    "durability": int(row["s_durability"]),
                    "reviews":    int(row["s_reviews"]),
                }
                score = calc_score(s["price"], s["perf"], s["durability"], s["reviews"])

                if verify and "score" in row and row["score"].strip():
                    csv_score = int(row["score"])
                    if csv_score != score:
                        errors.append(f"แถว {i} ({row['id']}): score ใน CSV = {csv_score}, คำนวณได้ = {score}")

                pros = [x.strip() for x in row["pros"].split("|") if x.strip()]
                cons = [x.strip() for x in row["cons"].split("|") if x.strip()]

                product = {
                    "id":      row["id"].strip(),
                    "cat":     row["cat"].strip(),
                    "sub":     row["sub"].strip(),
                    "brand":   row["brand"].strip(),
                    "name":    row["name"].strip(),
                    "img":     row.get("img", "").strip(),
                    "price":   int(row["price"]),
                    "old":     int(row.get("old", 0) or 0),
                    "score":   score,
                    "s":       s,
                    "rating":  float(row["rating"]),
                    "reviews": int(row["reviews"]),
                    "badge":   row.get("badge", "").strip(),
                    "pros":    pros,
                    "cons":    cons,
                    "links": {
                        "shopee": row.get("link_shopee", "").strip(),
                        "lazada": row.get("link_lazada", "").strip(),
                        "amazon": row.get("link_amazon", "").strip(),
                    },
                }
                products.append(product)

            except Exception as e:
                errors.append(f"แถว {i}: {e}")

    if errors:
        print("⚠️  พบข้อผิดพลาด:")
        for err in errors:
            print("  •", err)
        if not products:
            sys.exit(1)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"✅  แปลงสำเร็จ {len(products)} รุ่น → {out_path}")
    if errors:
        print(f"   (มีข้อผิดพลาด {len(errors)} รายการ กรุณาตรวจสอบด้านบน)")


def verify_scores(json_path: str):
    """ตรวจสอบ score ใน products.json ว่าตรงสูตรทุกรุ่น"""
    with open(json_path, encoding="utf-8") as f:
        products = json.load(f)
    errors = []
    for p in products:
        expected = calc_score(p["s"]["price"], p["s"]["perf"], p["s"]["durability"], p["s"]["reviews"])
        if p["score"] != expected:
            errors.append(f"{p['id']}: score={p['score']}, คำนวณได้={expected}")
    if errors:
        print(f"❌  พบ score ไม่ตรงสูตร {len(errors)} รุ่น:")
        for e in errors:
            print("  •", e)
    else:
        print(f"✅  score ถูกต้องทุกรุ่น ({len(products)} รุ่น)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KoomMeter CSV→JSON converter")
    parser.add_argument("input", nargs="?", help="CSV file path")
    parser.add_argument("-o", "--output", default="products.json", help="Output JSON path (default: products.json)")
    parser.add_argument("--verify", action="store_true", help="ตรวจสอบ score ว่าตรงสูตร")
    parser.add_argument("--verify-json", metavar="FILE", help="ตรวจสอบ score จาก products.json โดยตรง")
    args = parser.parse_args()

    if args.verify_json:
        verify_scores(args.verify_json)
    elif args.input:
        convert(args.input, args.output, args.verify)
    else:
        parser.print_help()
