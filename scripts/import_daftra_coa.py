#!/usr/bin/env python3
import argparse
import csv
import os

import frappe


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default=os.environ.get("SITE", "localhost"))
    parser.add_argument(
        "--csv",
        default="data/daftra/Journal Accounts.csv",
        help="Path relative to bench root",
    )
    args = parser.parse_args()

    bench_root = os.environ.get("BENCH_ROOT", "/home/frappe/frappe-bench")
    sites_path = os.path.join(bench_root, "sites")
    csv_path = args.csv
    if not os.path.isabs(csv_path):
        csv_path = os.path.join(bench_root, csv_path)

    frappe.init(site=args.site, sites_path=sites_path)
    frappe.connect()

    company = frappe.defaults.get_global_default("company") or frappe.get_all(
        "Company", pluck="name"
    )[0]
    abbr = frappe.db.get_value("Company", company, "abbr")

    root_type_map = {
        "1": ("Asset", "Balance Sheet"),
        "2": ("Liability", "Balance Sheet"),
        "3": ("Equity", "Balance Sheet"),
        "4": ("Income", "Profit and Loss"),
        "5": ("Expense", "Profit and Loss"),
    }

    root_parents = {
        "Asset": frappe.db.get_value(
            "Account",
            {"company": company, "account_name": "Application of Funds (Assets)"},
            "name",
        ),
        "Liability": frappe.db.get_value(
            "Account",
            {"company": company, "account_name": "Source of Funds (Liabilities)"},
            "name",
        ),
        "Equity": frappe.db.get_value(
            "Account", {"company": company, "account_name": "Equity"}, "name"
        ),
        "Income": frappe.db.get_value(
            "Account", {"company": company, "account_name": "Income"}, "name"
        ),
        "Expense": frappe.db.get_value(
            "Account", {"company": company, "account_name": "Expenses"}, "name"
        ),
    }

    corrections = {
        "60": ("5600", "مصروف الايجارات"),
        "61": ("5610", "مصروفات حكومية"),
        "62": ("5620", "رواتب وحوافز ومزايا الموظفين"),
        "63": ("5630", "صيانة ادارية وتشغيلية"),
        "64": ("5640", "مصروفات تسويقية"),
    }
    parent_override_prefix = {
        "60": "5600",
        "61": "5610",
        "62": "5620",
        "63": "5630",
        "64": "5640",
    }

    code_name: dict[str, str] = {}
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = (row.get("كود الحساب") or "").strip()
            name = (row.get("اسم الحساب") or "").strip()
            if not code or not name:
                continue
            if code in corrections:
                code, name = corrections[code]
            code_name[code] = name

    for root in ["1", "2", "3", "4", "5"]:
        code_name.setdefault(root, root)

    codes = set(code_name.keys())

    for old_code, (new_code, new_name) in corrections.items():
        old_doc = frappe.db.get_value(
            "Account", {"company": company, "account_number": old_code}, "name"
        )
        new_doc = frappe.db.get_value(
            "Account", {"company": company, "account_number": new_code}, "name"
        )
        if old_doc and not new_doc:
            new_docname = f"{new_code} - {new_name} - {abbr}"
            frappe.rename_doc("Account", old_doc, new_docname, force=True)
        elif old_doc and new_doc:
            frappe.delete_doc("Account", old_doc, ignore_permissions=True, force=True)

    parent_map: dict[str, str | None] = {}
    for code in codes:
        if code in ["1", "2", "3", "4", "5"]:
            parent_map[code] = None
            continue
        if code in ["5600", "5610", "5620", "5630", "5640"]:
            parent_map[code] = "5"
            continue
        for pref, parent in parent_override_prefix.items():
            if code.startswith(pref) and code != pref:
                parent_map[code] = parent
                break
        if code in parent_map:
            continue
        parent = None
        for i in range(len(code) - 1, 0, -1):
            p = code[:i]
            if p in codes:
                parent = p
                break
        parent_map[code] = parent

    children: dict[str, set[str]] = {}
    for code, parent in parent_map.items():
        if parent:
            children.setdefault(parent, set()).add(code)

    created = 0
    updated = 0

    for code in sorted(codes, key=lambda c: (len(c), c)):
        name = code_name[code]
        is_group = 1 if code in children else 0
        root_key = code[0]
        root_type, report_type = root_type_map.get(root_key, (None, None))

        parent_code = parent_map.get(code)
        if parent_code:
            parent_name = frappe.db.get_value(
                "Account",
                {"company": company, "account_number": parent_code},
                "name",
            )
        else:
            parent_name = root_parents.get(root_type)

        if not parent_name:
            raise RuntimeError(f"Missing parent for {code} ({name})")

        existing = frappe.db.get_value(
            "Account", {"company": company, "account_number": code}, "name"
        )
        if existing:
            doc = frappe.get_doc("Account", existing)
            doc.account_name = name
            doc.account_number = code
            doc.parent_account = parent_name
            doc.is_group = is_group
            if root_type:
                doc.root_type = root_type
            if report_type:
                doc.report_type = report_type
            doc.flags.ignore_permissions = True
            doc.save()
            updated += 1
        else:
            doc = frappe.new_doc("Account")
            doc.account_number = code
            doc.account_name = name
            doc.company = company
            doc.parent_account = parent_name
            doc.is_group = is_group
            if root_type:
                doc.root_type = root_type
            if report_type:
                doc.report_type = report_type
            doc.flags.ignore_permissions = True
            doc.insert()
            created += 1

    frappe.db.commit()
    print(f"REBUILD_DONE created={created} updated={updated}")

    frappe.destroy()


if __name__ == "__main__":
    main()
