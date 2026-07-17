# FaceTrack AI – Smart Attendance Management System

FaceTrack AI is a commercial-grade, production-quality, AI-powered Attendance Management System built with Python, Flask, OpenCV, SQLite, and custom Glassmorphism UI layout.

---

## Features

1. **Secure Admin Authentication**: BCrypt-equivalent secure hashed passwords, session handling, remember login persistence, and local database recovery instructions.
2. **Student Directory Database**: Full CRUD operations for student profiles, profile photo upload handles, and filter search features (by Name, Student ID, Department, Semester).
3. **Bulk CSV Import**: Import hundreds of student profiles instantly using the Pandas and OpenPyXL importer engine.
4. **Interactive Face Enrollment Wizard**: WebRTC client-side frame snapshot loop (50-100 snapshots) with pose guide alerts to train individual face encodings.
5. **Real-time Face recognition Terminal**: Browser-side canvas drawing matching boxes, voice synthesizer check-in alerts, and liveness analyses (Blink, Smile, Emotion, Face Mask detection).
6. **Executive Dashboard & Analytics**: Donut charts, weekly line trends, department distributions, emotion distributions, top performers lists, and at-risk student notifications.
7. **Reporting Console**: Dynamic filters (date range, department, status, specific student) to export custom PDF reports (ReportLab) or Excel sheets (Pandas/OpenPyXL).
8. **Database Checkpoints**: Create database backups and restore checkpoints directly from the administrator dashboard panel.

---

## Folder Structure

```
FaceTrackAI/
├── app.py                   # App entrypoint
├── config.py                # Configuration file
├── database.db              # SQLite Database file
├── requirements.txt         # Dependencies
│
├── models/
│   ├── db.py                # Database connection & table setup
│   ├── admin.py             # Admin profiles and validations
│   ├── student.py           # CRUD for students & bulk imports
│   └── attendance.py        # Attendance records (handled in db/routes)
│
├── routes/
│   ├── auth.py              # Login, logout blueprint
│   ├── students.py          # Student profile blueprint
│   ├── attendance.py        # Check-in and logs views
│   ├── dashboard.py         # Summary cards and analytics blueprints
│   ├── api.py               # Biometrics JSON API
│   └── settings.py          # Profiles & Backups blueprints
│
├── services/
│   ├── face_service.py      # Face detector & feature analyzer
│   ├── report_service.py    # ReportLab & OpenPyXL exporter engine
│   └── backup_service.py    # SQLite backup and restore utilities
│
├── static/
│   ├── css/
│   │   └── style.css        # Glassmorphic stylesheets
│   └── js/
│       └── main.js          # Shared scripts, themes, and dynamic toast alerts
│
├── templates/               # HTML5 layouts
│   ├── base.html            # Main dashboard shell
│   ├── auth/                # login & recover
│   ├── dashboard/           # stats & ratio donut
│   ├── students/            # directories & registration forms
│   ├── attendance/          # webcam terminal & lists
│   ├── analytics/           # trend lines & charts
│   ├── reports/             # export configurations
│   └── settings/            # profiles & checkpoints
│
├── dataset/                 # Raw frames folder
├── backup/                  # SQLite backup files
├── logs/                    # Standard logs folder
├── reports/                 # Compiled export PDFs
└── uploads/                 # Profile images
```

---

## Installation & Setup

### Prerequisites
1. Python 3.13 installed.
2. OpenCV prerequisites installed.
3. CMake (Optional: Only required if compiling `face_recognition` / `dlib` natively. If not present, the system runs automatically in **Haar Cascade Fallback Mode**).

### Setup Instructions
1. Clone or navigate to the project directory:
   ```bash
   cd "/Users/rushikeshjadhav/ai attendence"
   ```
2. Install standard dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Run environment diagnostics to verify everything compiles:
   ```bash
   python3 verify_setup.py
   ```
4. Start the application local server:
   ```bash
   python3 app.py
   ```
5. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5001
   ```
6. Sign in with the **Default Administrator Credentials**:
   * **Username**: `admin`
   * **Password**: `adminpassword`

---

## Database Schema (SQLite)

* **admins**: Stores administrative users, hashed credentials, and timestamp limits.
* **students**: Stores student profiles, departments, semesters, and profile images paths.
* **face_encodings**: Stores serialized 128D floating arrays mapped to student IDs.
* **attendance**: Logs check-in timestamp details, statuses (Present, Late), and AI analysis parameters (emotion, blink, smile, mask).
* **system_logs**: Stores debug log records shown on the dashboard panels.
* **settings**: Stores tolerance margins, camera indexing, and start times.

---

## API Endpoints

* `POST /api/register_face_frame/<student_id>`: Receives base64 image data during enrollment, computes face encoding, and saves to database.
* `POST /api/recognize_attendance`: Receives base64 camera frame, compares with known face profiles, registers daily attendance log if match is found, and returns AI features analysis.
* `POST /api/clear_encodings/<student_id>`: Clears enrolled biometric data for a student.

---

## User Manual

### 1. Registering Students
1. Navigate to **Students** in the sidebar.
2. Click **Add Student** (or select **Import CSV** to import a list).
3. Fill in the student profile details, upload an optional image, and submit.
4. Click **Enroll Face Biometrics** on their profile page to launch the registration feed.
5. Click **Start Enrollment** and follow the on-screen posing guide until the circle reaches 100%.

### 2. Marking Attendance
1. Navigate to **Face Scanner** in the sidebar.
2. Choose your active camera from the dropdown and click **Start Scanner**.
3. Point the terminal at the sign-in station. Once a student's face is recognized:
   * A green boundary outline appears.
   * A voice confirmation plays over the speakers.
   * Daily attendance logs are marked (with Present / Late checks).
   * Feature statistics (Emotion, smile, mask, blink) are computed in real-time.

### 3. Reporting & Database Checkpoints
1. Navigate to **Reports** to download zebra-striped print PDFs or spreadsheet Excel logs.
2. Navigate to **Settings** to adjust tolerance sliders, modify admin credentials, or trigger database checkpoints.
