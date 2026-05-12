# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistry

# Vietnamese uppercase + lowercase character sets
_VN_UP = r"A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ"
_VN_LO = r"a-záàảãạăắằẳẵặâấầẩẫậđéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ"

# Vietnamese name: 2-4 words, each starting with uppercase (ASCII or Vietnamese)
_VN_WORD = rf"[{_VN_UP}][{_VN_LO}]+"
_VN_NAME_REGEX = rf"{_VN_WORD}(?:\s+{_VN_WORD}){{1,3}}"


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """Xây dựng AnalyzerEngine với các recognizer tùy chỉnh cho VN."""

    # --- TASK 2.2.1 ---
    # CCCD VN: 12 chữ số; dự phòng 10-11 digit khi CSV đọc thành integer (mất leading zero)
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language="vi",
        patterns=[
            Pattern("cccd_12", regex=r"\b\d{12}\b", score=0.95),
            Pattern("cccd_11", regex=r"\b\d{11}\b", score=0.85),
            Pattern("cccd_10", regex=r"\b\d{10}\b", score=0.75),
        ],
        context=["cccd", "căn cước", "chứng minh", "cmnd"]
    )

    # --- TASK 2.2.2 ---
    # Số điện thoại VN: 0[35789]xxxxxxxx
    # Dự phòng khi mất leading 0 (đọc từ CSV integer)
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language="vi",
        patterns=[
            Pattern("vn_phone_full",   regex=r"\b0[35789]\d{8}\b", score=0.90),
            Pattern("vn_phone_nozero", regex=r"\b[35789]\d{8}\b",  score=0.80),
        ],
        context=["điện thoại", "sdt", "phone", "liên hệ"]
    )

    # Email recognizer cho "vi"
    email_recognizer = PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        supported_language="vi",
        patterns=[Pattern(
            name="email_vi",
            regex=r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b",
            score=0.90
        )],
        context=["email", "mail", "thư điện tử"]
    )

    # --- PERSON: tên người Việt (2-4 từ, mỗi từ viết hoa) ---
    person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        supported_language="vi",
        patterns=[Pattern(
            name="vn_person_name",
            regex=_VN_NAME_REGEX,
            score=0.70
        )],
        context=["bệnh nhân", "tên", "họ tên", "bác sĩ", "patient"]
    )

    # --- TASK 2.2.3 ---
    provider = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "vi",
                    "model_name": "vi_core_news_lg"}]
    })
    nlp_engine = provider.create_engine()

    # --- TASK 2.2.4 ---
    registry = RecognizerRegistry(supported_languages=["vi"])
    registry.add_recognizer(cccd_recognizer)
    registry.add_recognizer(phone_recognizer)
    registry.add_recognizer(email_recognizer)
    registry.add_recognizer(person_recognizer)

    analyzer = AnalyzerEngine(
        nlp_engine=nlp_engine,
        registry=registry,
        supported_languages=["vi"]
    )

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """Detect PII trong text tiếng Việt."""
    results = analyzer.analyze(
        text=text,
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE", "LOCATION"]
    )
    return results
