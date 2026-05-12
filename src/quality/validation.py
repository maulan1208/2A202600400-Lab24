# src/quality/validation.py
import pandas as pd
import re

def validate_anonymized_data(filepath: str) -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath)
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD gốc dạng số thuần túy 12 chữ số liên tiếp
    if "cccd" in df.columns:
        pure_numeric_cccd = df["cccd"].astype(str).str.match(r"^\d{12}$")
        if pure_numeric_cccd.any():
            results["success"] = False
            results["failed_checks"].append("CCCD column still contains raw numeric 12-digit values")

    # Check 2: Không có null values trong các cột quan trọng
    important_cols = [c for c in ["patient_id", "benh", "ket_qua_xet_nghiem"] if c in df.columns]
    for col in important_cols:
        if df[col].isnull().any():
            results["success"] = False
            results["failed_checks"].append(f"Column '{col}' has null values")

    # Check 3: Số rows phải bằng original (tối thiểu > 0)
    if len(df) == 0:
        results["success"] = False
        results["failed_checks"].append("Anonymized file has no rows")

    return results


def build_patient_expectation_suite():
    """Tạo expectation suite thủ công không dùng GX context để tránh lỗi version."""
    df = pd.read_csv("data/raw/patients_raw.csv")
    failed = []

    # 1. patient_id không null
    if df["patient_id"].isnull().any():
        failed.append("patient_id has nulls")

    # 2. cccd có đúng 12 ký tự
    wrong_len = df["cccd"].astype(str).str.len() != 12
    if wrong_len.any():
        failed.append(f"cccd wrong length: {wrong_len.sum()} rows")

    # 3. ket_qua_xet_nghiem trong khoảng [0, 50]
    out_of_range = ~df["ket_qua_xet_nghiem"].between(0, 50)
    if out_of_range.any():
        failed.append(f"ket_qua_xet_nghiem out of range: {out_of_range.sum()} rows")

    # 4. benh thuộc danh sách hợp lệ
    valid_conditions = {"Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"}
    invalid_benh = ~df["benh"].isin(valid_conditions)
    if invalid_benh.any():
        failed.append(f"benh has invalid values: {df.loc[invalid_benh, 'benh'].unique()}")

    # 5. email match regex
    email_regex = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    invalid_email = ~df["email"].astype(str).str.match(email_regex)
    if invalid_email.any():
        failed.append(f"email format invalid: {invalid_email.sum()} rows")

    # 6. patient_id unique
    if df["patient_id"].duplicated().any():
        failed.append("patient_id has duplicates")

    return {"passed": len(failed) == 0, "failures": failed, "total_rows": len(df)}
