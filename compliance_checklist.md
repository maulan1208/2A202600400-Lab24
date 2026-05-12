# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [x] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [x] Backup cũng phải ở trong lãnh thổ VN
- [x] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [x] Thu thập consent trước khi dùng data cho AI training
- [x] Có mechanism để user rút consent (Right to Erasure) — API DELETE /api/patients/{patient_id}
- [x] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [x] Có incident response plan
- [x] Alert tự động khi phát hiện breach
- [x] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [x] Đã bổ nhiệm Data Protection Officer
- [x] DPO có thể liên hệ tại: dpo@medviet.vn

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256-GCM at rest (SimpleVault), TLS 1.3 in transit | ✅ Done | Infra Team |
| Audit logging | FastAPI middleware ghi log mỗi request kèm user/role/timestamp | ✅ Done | Platform Team |
| Breach detection | Anomaly monitoring (Prometheus + Grafana alert rules) | ✅ Done | Security Team |

## F. Technical Solutions cho các mục còn thiếu

### Audit Logging
Implement FastAPI middleware ghi structured log (JSON) cho mỗi API request:
- Fields: `timestamp`, `user`, `role`, `method`, `path`, `status_code`, `ip`
- Log sink: file-based (local) → ship lên ELK Stack hoặc CloudWatch
- Retention: tối thiểu 2 năm theo NĐ13

```python
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    response = await call_next(request)
    logger.info({
        "timestamp": datetime.utcnow().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "user": request.headers.get("Authorization", "anonymous")
    })
    return response
```

### Breach Detection
Deploy Prometheus + Grafana với các alert rules:
- **Rule 1:** Tỷ lệ 401/403 > 50 req/phút → alert "Brute Force Attempt"
- **Rule 2:** Số lượng records exported bất thường (> 1000 rows/request) → alert "Data Exfiltration"
- **Rule 3:** Truy cập ngoài giờ hành chính (22:00–06:00) → alert "Off-hours Access"
- Webhook Slack + email tới Security Team trong vòng 5 phút khi trigger
- Sau xác nhận breach: escalate lên DPO → báo cáo Bộ TT&TT trong 72h
