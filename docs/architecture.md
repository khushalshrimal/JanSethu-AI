# JanSethu AI 2.0 Architectural Specification

## Authentication & Security Architecture

```
+-------------------------------------------------------------+
|                      CLIENT REQUEST                         |
|        Headers: Authorization: Bearer <JWT_TOKEN>           |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                 SECURITY DEPENDENCY (deps.py)               |
|  1. Decode JWT HS256 signature using SECRET_KEY             |
|  2. Extract sub (user_id) & check token expiration           |
|  3. Fetch User from DB & verify is_active == True           |
|  4. Check require_roles(*allowed_roles) [RBAC]              |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                 CONTROLLER / ROUTE HANDLER                  |
|  5. Object-Level Authorization Check                        |
|     (e.g., appointment.patient_id == user.patient_profile.id)|
|  6. Log Security Action to AuditLog table                   |
+-------------------------------------------------------------+
```
