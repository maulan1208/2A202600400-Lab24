# src/pii/anonymizer.py
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        TODO: Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        # TODO: implement operators dict dựa trên strategy
        operators = {}

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", 
                          {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", 
                                 {"new_value": fake.email()}),   # TODO: fake email
                "VN_CCCD": OperatorConfig("replace", 
                           {"new_value": fake.bothify(text='############')}),          # TODO: fake CCCD
                "VN_PHONE": OperatorConfig("replace", 
                            {"new_value": fake.phone_number()}),         # TODO: fake phone
            }
        elif strategy == "mask":
            operators = {
                "DEFAULT": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 8, "from_end": True})
            }
        elif strategy == "hash":
            operators = {
                "DEFAULT": OperatorConfig("hash", {"hash_type": "sha256"})
            }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TODO: Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        # TODO: Xử lý từng cột PII
        # Gợi ý: dùng df.apply() hoặc list comprehension
        
        df_anon['ho_ten'] = df_anon['ho_ten'].apply(lambda x: self.anonymize_text(x))
        df_anon['dia_chi'] = df_anon['dia_chi'].apply(lambda x: self.anonymize_text(x))
        df_anon['email'] = df_anon['email'].apply(lambda x: self.anonymize_text(x))

        # Thay thế trực tiếp các cột có cấu trúc cố định để đảm bảo 100% an toàn
        df_anon['cccd'] = [fake.bothify(text='############') for _ in range(len(df))]
        df_anon['so_dien_thoai'] = [fake.phone_number() for _ in range(len(df))]

        return df_anon

    def calculate_detection_rate(self,
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công. Mục tiêu: > 95%
        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        # Padding spec: CCCD=12 digits, phone=10 digits (leading zeros lost in CSV)
        pad_spec = {"cccd": 12, "so_dien_thoai": 10}

        total = 0
        detected = 0

        for col in pii_columns:
            pad_len = pad_spec.get(col, 0)
            for value in original_df[col].astype(str):
                total += 1
                # Restore leading zeros stripped when CSV reads numbers as integers
                if pad_len and value.isdigit():
                    value = value.zfill(pad_len)
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
