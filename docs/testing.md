# JanSethu AI 2.0 Testing Documentation

> "Do not trust a screen. Verify the underlying state."

## Phase 2 Test Coverage
1. **Customer Registration**: `test_customer_registration_and_duplicate_reject` tests customer registration and 409 Conflict rejection on duplicate phone number.
2. **JWT Authentication**: `test_login_and_jwt_issuance` tests phone/password login, JWT access token issuance, `/auth/me` with valid token, and 401 Unauthorized rejection on invalid password/phone.
3. **Role-Based Access Control (RBAC)**: `test_role_based_access_control` tests Customer attempting `POST /facilities/` (asserts HTTP 403 Forbidden) vs Admin attempting `POST /facilities/` (asserts HTTP 201 Created).
4. **Object-Level Authorization**: `test_object_level_authorization` tests Customer A attempting to view Customer B's appointment via `GET /appointments/{id}` (asserts HTTP 403 Forbidden).

## Running Complete Test Suite
```bash
cd backend
python -m unittest discover -s app/tests -p "test_*.py"
```
