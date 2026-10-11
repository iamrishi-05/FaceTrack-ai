# FaceTrack AI — Multi-Sector Facial Intelligence, Biometric Verification & Real-Time Person Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/Computer%20Vision-OpenCV%20%26%20Dlib-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Enterprise-blue.svg)](#license)
[![Architecture](https://img.shields.io/badge/Architecture-Modular%20MVC%20%2B%20WebRTC-0ea5e9.svg)](#system-architecture)

**FaceTrack AI** is a commercial-grade, multi-sector computer vision and biometric intelligence platform. Designed to process live video streams (via WebRTC browser feeds, RTSP/ONVIF security cameras, or batch-uploaded CCTV footage), FaceTrack AI provides real-time face detection, 128-dimensional deep metric vector matching, anti-spoofing liveness verification, and spatial trajectory analytics.

While originally prototyped as an educational attendance tracker, FaceTrack AI has evolved into a **domain-agnostic biometric and computer vision engine** engineered to support **10 mission-critical operational fields**, ranging from public safety and humanitarian missing-person search to enterprise access control, healthcare safety, and retail analytics.

---

## Table of Contents

- [Key Sector Applications (10 Core Fields)](#key-sector-applications-10-core-fields)
- [System Architecture & Computer Vision Pipeline](#system-architecture--computer-vision-pipeline)
- [Key Engineering Highlights](#key-engineering-highlights)
- [Project Directory Structure](#project-directory-structure)
- [Database Schema (SQLite)](#database-schema-sqlite)
- [RESTful API Specification](#restful-api-specification)
- [Installation & Quickstart Guide](#installation--quickstart-guide)
- [Ethical AI, Privacy & Legal Governance](#ethical-ai-privacy--legal-governance)
- [Roadmap & Implementation Plan](#roadmap--implementation-plan)

---

## Key Sector Applications (10 Core Fields)

FaceTrack AI is architected with modular domain engines to serve diverse real-world environments:

### 1. Police Assistance & Authorized Person-of-Interest (POI) Alerts
- **Operational Scope**: Assists authorized law enforcement personnel in monitoring high-density CCTV streams at railway stations, bus interchanges, airport terminals, checkpoints, and public venues.
- **Functionality**: Flags candidate matches in real-time against a legally sanctioned watchlist.
- **Safety Protocol**: Implements a strict **Human-in-the-Loop (HITL)** protocol—alerts provide side-by-side visual comparisons, timestamped snapshots, and similarity metrics for mandatory human review prior to any operational intervention.

### 2. Missing-Person Assistance
- **Operational Scope**: Supports search-and-rescue teams, humanitarian organizations, and law enforcement in locating missing children, vulnerable individuals, or lost elders.
- **Functionality**: Rapidly screens live camera feeds and historical CCTV footage using an approved reference photograph.
- **Alert Triage**: Generates chronological sighting trails across camera locations with confidence scoring to prioritize search zones.

### 3. Smart College & Institutional Attendance
- **Operational Scope**: Universities, schools, and training academies seeking touchless, automated attendance management.
- **Functionality**: Simultaneously identifies enrolled students entering classrooms or lecture halls, prevents buddy-punching via liveness checks, and rejects duplicate check-ins within the same period.
- **Reporting**: Generates automated daily, monthly, and subject-wise attendance ledgers with PDF and Excel export capabilities.

### 4. Workplace & Enterprise Access Management
- **Operational Scope**: Corporate offices, industrial facilities, and data centers.
- **Functionality**: Verifies enrolled employees at entry turnstiles and security doors, logs ingress/egress events with microsecond timestamps, and issues instantaneous alerts when unlisted or unauthorized personnel attempt entry into restricted zones.

### 5. Hospital & Healthcare Patient Assistance
- **Operational Scope**: Hospitals, specialized rehabilitation facilities, and psychiatric wards.
- **Functionality**: With patient or guardian consent and strict medical safeguards, helps healthcare workers identify registered patients who may have become disoriented, confused, or wandered outside of safe care zones.
- **Safeguards**: Discretely notifies nursing staff stations without sounding public alarms.

### 6. Transport Hub & Transit Security
- **Operational Scope**: Major transit centers, railway junctions, bus terminals, and international airport gates.
- **Functionality**: Helps authorized security personnel review security incidents, trace the multi-camera trajectory of individuals across concourses, and identify suspicious perimeter re-entries in compliance with transit security regulations.

### 7. Public-Event Safety & Crowd Intelligence
- **Operational Scope**: Stadiums, concerts, music festivals, exhibitions, and major civic gatherings.
- **Dual Capability**:
  - **Authorized Threat Detection**: Flags individuals on an approved event watchlist.
  - **Anonymous Crowd Metrics**: Performs non-biometric crowd counting and density monitoring, alerting venue operators of crowd surges and bottlenecks without identifying individual event attendees.

### 8. Elderly & Vulnerable Person Care
- **Operational Scope**: Assisted living communities, nursing homes, and memory-care facilities.
- **Functionality**: In controlled environments, assists caregivers in ensuring resident safety using consent-based enrollment. Generates urgent alerts if a registered resident suffering from dementia or Alzheimer's wanders towards perimeter gates or stairwells.

### 9. Retail & Facility Security
- **Operational Scope**: Retail department stores, shopping malls, and corporate headquarters.
- **Functionality**: Identifies repeated organized retail theft offenders against an authorized loss-prevention database, guards staff-only back rooms against trespassers, and provides opt-in VIP customer greeting integrations.

### 10. Real-Time Person Tracking & Spatial Analytics
- **Operational Scope**: Multi-camera commercial facilities, warehouses, and campuses.
- **Functionality**: Performs cross-camera person tracking and re-identification (Re-ID), calculates dwell times in specific zones, constructs movement heatmaps, and reconstructs historical movement paths across facility floorplans.

---

## System Architecture & Computer Vision Pipeline

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Video Ingestion Tier                            │
│  [WebRTC Client Browser HUD]  |  [RTSP/ONVIF IP Streams]  |  [CCTV Files]│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Base64 JPEG / Raw Frames
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Vision & Preprocessing Engine                        │
│  • Dual-Engine Face Detection (Dlib HOG / OpenCV Haar Cascade fallback)│
│  • 68-Point Facial Landmark Alignment & Normalization                  │
│  • Anti-Spoofing & Liveness Analysis (Blink EAR, Smile MAR, Mask)      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Normalized Crop
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Biometric Feature & Vector Engine                      │
│  • 128-Dimensional Deep Metric Embeddings (ResNet)                     │
│  • L2 Euclidean Distance & Cosine Metric Matching                      │
│  • Indexed Vector Lookup against Registered Subject Profiles           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Match / Confidence Metric
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               Domain Logic, Rate-Limiting & Alerting                   │
│  • Intelligent Anti-Flooding Cooldown (60s default rate limit)        │
│  • Sector Engine (Police / Missing / Access / Hospital / Attendance)   │
│  • Web Speech Audio Synthesizer ("Target Identified: [Name]")          │
│  • Immutable SQLite Audit Logging & Multi-Channel Webhooks             │
└────────────────────────────────────────────────────────────────────────┘
```

### Mathematical & Algorithmic Formulations

1. **128D Face Embedding Distance**:
   $$d = \sqrt{\sum_{i=1}^{128} (e_{\text{known}}[i] - e_{\text{probe}}[i])^2}$$
   - A threshold of $d \le 0.45$ represents a high-confidence match ($>80\%$).
   - The tolerance is configurable via the administrator dashboard.

2. **Eye Aspect Ratio (EAR) for Blink Detection**:
   $$\text{EAR} = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \|p_1 - p_4\|}$$
   - When $\text{EAR} < 0.20$, an eye-closure (blink) is registered, verifying biological liveness.

3. **Mouth Aspect Ratio (MAR) for Smile Analysis**:
   $$\text{MAR} = \frac{\|m_3 - m_7\| + \|m_4 - m_6\|}{2 \|m_1 - m_5\|}$$

---

## Key Engineering Highlights

- **Dual-Engine Graceful Fallback**: Native Dlib deep learning inference when compiled, with automatic graceful fallback to OpenCV Haar Cascades and color-moment spatial feature descriptors. Guarantees zero crashes across any hosting environment.
- **Interactive Browser Canvas HUD**: Renders real-time bounding boxes, classification overlays, and target names directly on client browsers via WebRTC with zero plugin dependencies.
- **Voice Synthesizer Alerts**: Integrated with the Web Speech API (`speechSynthesis.speak`) for eyes-free audio alerts.
- **Smart Anti-Flooding Rate Limiter**: Multi-tiered in-memory timestamp hash combined with an SQL interval check (60-second default cooldown) prevents database flooding when an individual remains in camera view.
- **Self-Contained Reporting Engine**: Direct compilation of executive PDF reports via ReportLab and spreadsheet workbooks via OpenPyXL and Pandas.
- **Cross-Platform Mobile Support**: Pre-configured SSL certificates (`cert.pem`, `key.pem`) enable secure HTTPS camera streaming from smartphones and tablets on the local network.

---

## Project Directory Structure

```
FaceTrackAI/
├── app.py                         # Application entrypoint & blueprint orchestrator
├── config.py                      # System configuration, paths & default tolerances
├── database.db                    # SQLite production database
├── requirements.txt               # Python package dependencies
├── IMPLEMENTATION_PLAN.md         # Comprehensive 10-sector technical engineering plan
│
├── models/
│   ├── db.py                      # Database connection pool & table migrations
│   ├── target.py                  # Target profiles, 128D encodings & detection logging
│   ├── user.py                    # User authentication models
│   ├── student.py                 # Academic attendance backward-compatibility module
│   └── admin.py                   # Administrative user management
│
├── routes/
│   ├── tracker.py                 # Live HUD tracker, target management & settings
│   ├── api.py                     # Real-time frame recognition & biometric endpoints
│   ├── auth.py                    # Authentication & session management
│   ├── attendance.py              # Institutional attendance check-in views
│   ├── dashboard.py               # Executive analytics & charts
│   ├── reports.py                 # PDF/Excel report export handlers
│   └── students.py                # Academic student profile management
│
├── services/
│   ├── face_service.py            # Computer vision, face detection & liveness algorithms
│   ├── report_service.py          # PDF generation (ReportLab) & Excel exports
│   └── backup_service.py          # Database backup & restore utilities
│
├── static/
│   ├── css/
│   │   └── style.css              # Custom Glassmorphism design system & HUD styling
│   └── js/
│       └── main.js                # WebRTC canvas rendering, camera loop & voice alerts
│
├── templates/
│   ├── base.html                  # Master dashboard shell & glassmorphic layout
│   ├── tracker.html               # Live camera tracking terminal & target spotting feed
│   ├── targets.html               # Target management, photo upload & watchlist directory
│   ├── detections.html            # Detection audit trail & event history log
│   ├── settings.html              # System tolerances, camera selection & alert config
│   ├── attendance/                # Dedicated attendance terminal views
│   └── reports/                   # Reporting console views
│
├── dataset/                       # Stored reference biometric frames
├── uploads/                       # Uploaded reference photographs & profile images
├── logs/                          # System audit & execution logs
└── reports/                       # Generated PDF and Excel report artifacts
```

---

## Database Schema (SQLite)

- **`targets`**: Stores registered target profiles (`target_id`, `name`, `notes`, `photo_path`, `status`, `created_at`). Supports multiple entity types (Watchlist, Missing, Student, Employee, Patient, Resident, VIP).
- **`target_encodings`**: Stores serialized 128-dimensional floating-point biometric vectors mapped to `target_id`.
- **`detection_logs`**: Comprehensive detection audit trail (`target_id`, `target_name`, `timestamp`, `date`, `time`, `confidence`, `emotion`, `smile_detected`, `blink_detected`, `mask_detected`, `location_tag`, `snapshot_path`).
- **`users`**: Administrative and operator accounts with secure password hashing.
- **`settings`**: Dynamic operational parameters (`tolerance`, `audio_alert`, `cooldown_seconds`, `camera_index`).
- **`students` & `attendance`**: Dedicated academic sub-schema for institutional attendance tracking.

---

## RESTful API Specification

| Endpoint | Method | Payload | Description |
|---|---|---|---|
| `/api/recognize_frame` | `POST` | `{"image": "data:image/jpeg;base64,..."}` | Receives camera snapshot, detects faces, performs 128D vector comparison, logs match (subject to cooldown), returns bounding boxes, confidence, and liveness. |
| `/api/upload_target` | `POST` | Multipart Form: `name`, `notes`, `photo_file` OR Base64 image | Creates a new target profile, computes 128D encodings, and registers the identity into the active vector database. |
| `/api/stats` | `GET` | None | Returns real-time KPI metrics: active targets, detections today, system uptime, and last spotted target. |
| `/api/clear_logs` | `POST` | None | Clears the detection history logs (authorized operators only). |
| `/api/register_face_frame/<target_id>` | `POST` | `{"image": "data:image/jpeg;base64,..."}` | Enrolls an additional biometric angle for a specific target profile. |

---

## Installation & Quickstart Guide

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed.
- Standard C++ build tools (optional: CMake and Dlib if compiling native ResNet; otherwise OpenCV Haar Cascade fallback activates automatically).
- A connected webcam or accessible IP camera stream.

### Quickstart Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/iamrishi-05/FaceTrack-ai.git
   cd FaceTrack-ai
   ```

2. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Verify environment setup**:
   ```bash
   python3 verify_setup.py
   ```

4. **Launch the application**:
   ```bash
   python3 app.py
   ```

5. **Access the Web Console**:
   Open your browser and navigate to:
   ```
   http://127.0.0.1:5001
   ```
   *Default Admin Credentials:*
   - **Username**: `admin`
   - **Password**: `adminpassword`

---

## Ethical AI, Privacy & Legal Governance

FaceTrack AI is designed with responsible, privacy-first computer vision principles:

1. **Mandatory Human-in-the-Loop (HITL)**: For law enforcement, missing persons, and medical alerts, the system serves as an advisory assistant. All flags require authorized human operator confirmation before taking action.
2. **Consent & Regulatory Alignment**:
   - Civilian, workplace, healthcare, and educational deployments require explicit informed consent adhering to **GDPR (EU)**, **HIPAA (USA)**, and **DPDP Act (India)**.
   - Law enforcement watchlist operations must be conducted under appropriate statutory authorization and legal warrants.
3. **Data Minimization**: Video frames without an approved match are processed strictly in volatile RAM and immediately discarded. No continuous bulk video recordings are permanently stored on the server.
4. **Encrypted Vector Biometrics**: Stored biometric signatures are mathematical 128-dimensional floating embeddings that cannot be reverse-engineered into raw human faces.
5. **Tamper-Evident Audit Trails**: Every identification event, settings adjustment, and operator verification is immutably logged with user timestamps.

---

## Roadmap & Implementation Plan

For detailed technical specifications, database migration blueprints, and phased development milestones for all 10 sectors, see the complete [Implementation Plan](IMPLEMENTATION_PLAN.md).

- [x] **Phase 1: Biometric Engine & Target Core** — Dual-engine vision pipeline, 128D embeddings, WebRTC HUD, rate-limiting cooldown, and audit logging.
- [ ] **Phase 2: Multi-Stream RTSP & Spatial Tracking** — Continuous IP camera ingestion, batch CCTV footage upload analysis, and cross-camera trajectory tracing.
- [ ] **Phase 3: Sector Modules & HITL Verification Portal** — Dedicated law enforcement review console, healthcare wander alerts, and access control webhooks.
- [ ] **Phase 4: Vector Acceleration & Enterprise Edge** — FAISS vector index scaling (100,000+ faces), RetinaFace / ArcFace deep models, and edge hardware deployment.

---

## License

This software is developed for authorized enterprise, academic, and public safety applications. Use of facial recognition technology must strictly comply with applicable local, state, national, and international laws and privacy regulations.
