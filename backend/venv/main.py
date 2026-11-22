from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from typing import Optional
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="barangay-complaints_db"
        )
        return connection
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return None


def write_audit_log(conn, action: str, details: str, user_id: Optional[int] = None):
    """Mag-insert ng log entry sa audit_logs (user_id, action, details, created_at)."""
    try:
        resolved_user_id = user_id
        if resolved_user_id is None:
            u_cur = conn.cursor()
            u_cur.execute("SELECT user_id FROM users ORDER BY user_id ASC LIMIT 1")
            row = u_cur.fetchone()
            u_cur.close()
            if row:
                resolved_user_id = row[0]

        log_cur = conn.cursor()
        log_cur.execute(
            """
            INSERT INTO audit_logs (user_id, action, details, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (resolved_user_id, action, details, datetime.now())
        )
        log_cur.close()
    except Exception as e:
        print(f"Audit log error: {e}")


# --- PYDANTIC MODELS ---

class SignupModel(BaseModel):
    full_name: str
    phone_number: str
    email: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class ComplaintModel(BaseModel):
    user_id: int
    complainant_name: str
    respondent_name: str
    complaint_details: str
    evidence_image: Optional[str] = None

class StatusUpdateModel(BaseModel):
    status: Optional[str] = None
    hearing_notes: Optional[str] = None

class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    hearing_notes: Optional[str] = None

class ArchiveUpdateModel(BaseModel):
    is_archived: bool


@app.post("/api/signup")
def signup(data: SignupModel):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT user_id FROM users WHERE contact_number = %s", (data.phone_number,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ang phone number na ito ay nakarehistro na.")

        cursor.execute("SELECT user_id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ang email na ito ay nagamit na ng ibang residente.")

        query = "INSERT INTO users (username, contact_number, email, password, role) VALUES (%s, %s, %s, %s, 'resident')"
        cursor.execute(query, (data.full_name, data.phone_number, data.email, data.password))
        conn.commit()

        return {"message": "User registered successfully!"}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.post("/api/login")
def login(data: LoginModel):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (data.username, data.password))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=400, detail="Mali ang buong pangalan o password.")

        return {
            "message": "Login Successful!",
            "user_id": user['user_id'],
            "role": user['role'],
            "username": user['username']
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/api/users/{user_id}")
def get_user_profile(user_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id, username, email, contact_number FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# --- PAG-SUMITE NG REKLAMO (MAY EBIDENSYA) ---
@app.post("/api/complaints")
def create_complaint(data: ComplaintModel):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO complaints (user_id, complainant_name, respondent_name, complaint_details, evidence_image, status, is_archived)
            VALUES (%s, %s, %s, %s, %s, 'Pending', 0)
        """
        cursor.execute(query, (
            data.user_id,
            data.complainant_name,
            data.respondent_name,
            data.complaint_details,
            data.evidence_image
        ))
        conn.commit()
        return {"message": "Reklamo at ebidensya ay matagumpay na naisumite!"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


# --- PAGKUHA NG MGA REKLAMO (MAY SUPORTA SA include_archived) ---
@app.get("/api/complaints")
def get_all_complaints(include_archived: bool = False):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        if include_archived:
            cursor.execute("SELECT * FROM complaints ORDER BY complaint_id DESC")
        else:
            cursor.execute("SELECT * FROM complaints WHERE (is_archived = 0 OR is_archived IS NULL) ORDER BY complaint_id DESC")
        result = cursor.fetchall()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/api/complaints/{complaint_id}")
def get_single_complaint(complaint_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM complaints WHERE complaint_id = %s", (complaint_id,))
        complaint = cursor.fetchone()
        if not complaint:
            raise HTTPException(status_code=404, detail="Hindi nahanap ang kaso.")
        return complaint
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.put("/api/complaints/{complaint_id}/status")
def update_complaint_status(complaint_id: int, data: StatusUpdateModel):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT status, hearing_notes FROM complaints WHERE complaint_id = %s", (complaint_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Hindi nahanap ang kaso.")

        new_status = data.status if data.status is not None else current[0]
        new_notes = data.hearing_notes if data.hearing_notes is not None else current[1]

        cursor.execute(
            "UPDATE complaints SET status = %s, hearing_notes = %s WHERE complaint_id = %s",
            (new_status, new_notes, complaint_id)
        )
        write_audit_log(
            conn,
            action="Update Case",
            details=f"Case #{complaint_id}: status -> '{new_status}', notes -> '{new_notes or ''}'"
        )
        conn.commit()
        return {"message": "Matagumpay na nabago ang status ng kaso."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.put("/api/complaints/{complaint_id}")
def update_complaint_details(complaint_id: int, data: ComplaintUpdate):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT status, hearing_notes FROM complaints WHERE complaint_id = %s", (complaint_id,))
        current = cursor.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail="Hindi nahanap ang kaso.")

        new_status = data.status if data.status is not None else current[0]
        new_notes = data.hearing_notes if data.hearing_notes is not None else current[1]

        query = "UPDATE complaints SET status = %s, hearing_notes = %s WHERE complaint_id = %s"
        cursor.execute(query, (new_status, new_notes, complaint_id))
        write_audit_log(
            conn,
            action="Update Case",
            details=f"Case #{complaint_id}: status -> '{new_status}', notes -> '{new_notes or ''}'"
        )
        conn.commit()

        return {"message": "Matagumpay na na-update ang kaso at status!"}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.put("/api/complaints/{complaint_id}/archive")
def toggle_archive_complaint(complaint_id: int, data: ArchiveUpdateModel):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT complaint_id FROM complaints WHERE complaint_id = %s", (complaint_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Hindi nahanap ang kaso.")

        archived_val = 1 if data.is_archived else 0
        cursor.execute(
            "UPDATE complaints SET is_archived = %s WHERE complaint_id = %s",
            (archived_val, complaint_id)
        )
        write_audit_log(
            conn,
            action="Archive Case" if archived_val == 1 else "Unarchive Case",
            details=f"Case #{complaint_id} {'archived' if archived_val == 1 else 'unarchived'}."
        )
        conn.commit()
        action = "na-archive" if archived_val == 1 else "na-unarchive"
        return {"message": f"Matagumpay na {action} ang kaso.", "is_archived": data.is_archived}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.delete("/api/complaints/{complaint_id}")
def delete_complaint(complaint_id: int):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT complaint_id FROM complaints WHERE complaint_id = %s", (complaint_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Hindi nahanap ang kaso.")

        cursor.execute("DELETE FROM complaints WHERE complaint_id = %s", (complaint_id,))
        conn.commit()
        return {"message": "Matagumpay na nabura ang kaso."}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/api/audit-logs")
def get_audit_logs():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM audit_logs ORDER BY log_id DESC")
        result = cursor.fetchall()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()
def write_audit_log(conn, action: str, details: str, user_id: Optional[int] = None):
    """Mag-insert ng log entry sa audit_logs gamit ang valid user_id mula sa users table."""
    try:
        resolved_user_id = user_id
        if resolved_user_id is None:
            u_cur = conn.cursor()
            u_cur.execute(
                """
                SELECT user_id FROM users
                ORDER BY CASE WHEN LOWER(role) = 'admin' THEN 0 ELSE 1 END, user_id ASC
                LIMIT 1
                """
            )
            row = u_cur.fetchone()
            u_cur.close()
            if not row:
                print("Audit log skipped: walang user record sa users table.")
                return
            resolved_user_id = row[0]

        log_cur = conn.cursor()
        log_cur.execute(
            """
            INSERT INTO audit_logs (user_id, action, details, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            (resolved_user_id, action, details, datetime.now())
        )
        log_cur.close()
    except Exception as e:
        print(f"Audit log error: {e}")