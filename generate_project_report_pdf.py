import os
import sys
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and draw total page count
    along with running header and footer.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        width, height = letter
        
        # Don't draw running header on cover/first page
        if self._pageNumber > 1:
            self.saveState()
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            
            # Running Header
            self.drawString(54, height - 36, "FaceTrack AI — Engineering Project Report & Architecture Specification")
            self.drawRightString(width - 54, height - 36, "Confidential & Academic")
            
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.6)
            self.line(54, height - 42, width - 54, height - 42)
            
            # Running Footer
            self.line(54, 46, width - 54, 46)
            page_str = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(width - 54, 32, page_str)
            self.drawString(54, 32, "FaceTrack AI — Real-Time Computer Vision & Biometrics")
            self.restoreState()


def build_pdf(filename="FaceTrack_AI_Project_Report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    COLOR_PRIMARY = colors.HexColor("#0f172a")    # Deep Navy / Slate
    COLOR_ACCENT = colors.HexColor("#059669")     # Emerald Green
    COLOR_SECONDARY = colors.HexColor("#2563eb")  # Cyber Blue
    COLOR_DARK = colors.HexColor("#1e293b")
    COLOR_MUTED = colors.HexColor("#64748b")
    COLOR_BG_LIGHT = colors.HexColor("#f8fafc")
    COLOR_BORDER = colors.HexColor("#e2e8f0")
    COLOR_BOX_BG = colors.HexColor("#f1f5f9")
    
    # Custom Paragraph Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=COLOR_PRIMARY,
        alignment=0,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=COLOR_ACCENT,
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=COLOR_PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=COLOR_ACCENT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=COLOR_DARK,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=COLOR_DARK,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )
    
    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=COLOR_PRIMARY
    )
    
    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0f172a")
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=COLOR_DARK
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # ==========================
    # COVER / HEADER BANNER
    # ==========================
    story.append(Paragraph("FACETRACK AI", title_style))
    story.append(Paragraph("Multi-Sector Facial Intelligence, Biometric Verification & Real-Time Person Analytics Platform", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=COLOR_ACCENT, spaceAfter=12))

    # Metadata Summary Box
    meta_data = [
        [
            Paragraph("<b>Project Domain:</b> Multi-Sector Computer Vision & Biometrics", table_cell_style),
            Paragraph("<b>Architecture:</b> Modular MVC + WebRTC Stream HUD", table_cell_style)
        ],
        [
            Paragraph("<b>Primary Backend:</b> Python 3.10+ / OpenCV / Dlib ResNet", table_cell_style),
            Paragraph("<b>Storage:</b> SQLite Relational Database & Vector Vault", table_cell_style)
        ],
        [
            Paragraph("<b>Date of Report:</b> " + datetime.now().strftime("%B %d, %Y"), table_cell_style),
            Paragraph("<b>Operational Scope:</b> 10 Enterprise & Public Safety Sectors", table_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BOX_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # ==========================
    # 1. EXECUTIVE SUMMARY & ABSTRACT
    # ==========================
    story.append(Paragraph("1. Executive Summary & Abstract", h1_style))
    story.append(Paragraph(
        "<b>FaceTrack AI</b> is a commercial-grade, multi-sector Computer Vision and Facial Intelligence platform "
        "engineered to deliver real-time person detection, 128-dimensional deep metric vector matching, anti-spoofing "
        "liveness verification, and spatial trajectory analytics across <b>10 critical operational fields</b>. "
        "While initially conceived as an institutional attendance tracker, the platform's core architecture has been "
        "generalized into a domain-agnostic biometric engine capable of processing video frames from client WebRTC "
        "streams, RTSP/ONVIF security cameras, and archival CCTV footage.",
        body_style
    ))
    story.append(Paragraph(
        "The system decodes incoming video buffers, computes 128-dimensional Euclidean facial embeddings using a Deep "
        "Residual Network (ResNet), checks identities against indexed reference profiles, and performs concurrent "
        "<b>liveness and feature analysis</b> (Eye Blink EAR, Smile MAR, Emotion classification, and Mask detection). "
        "To guarantee zero service disruptions across diverse CPU and server environments, FaceTrack AI incorporates a "
        "<b>Dual-Engine Fallback Pipeline</b> that seamlessly cascades from Dlib's 68-point landmark model to OpenCV "
        "Haar Cascades with spatial color-moment descriptors whenever native deep-learning dependencies are unavailable.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # ==========================
    # 2. OPERATIONAL SCOPE ACROSS 10 CORE SECTORS
    # ==========================
    story.append(Paragraph("2. Operational Scope Across 10 Core Industry Sectors", h1_style))
    story.append(Paragraph(
        "FaceTrack AI provides configurable domain engines tailored for distinct real-world environments:",
        body_style
    ))

    sector_table_data = [
        [Paragraph("Sector", table_header_style), Paragraph("Primary Objective & Operational Workflow", table_header_style), Paragraph("Safety / Privacy Protocol", table_header_style)],
        [
            Paragraph("<b>1. Police Assistance & POI Alerts</b>", table_cell_style),
            Paragraph("Review CCTV footage in crowded railway stations, bus stands, and checkpoints; flag matches against authorized watchlists.", table_cell_style),
            Paragraph("Mandatory Human-in-the-Loop (HITL) review before field action.", table_cell_style)
        ],
        [
            Paragraph("<b>2. Missing-Person Assistance</b>", table_cell_style),
            Paragraph("Scan live and historical footage using approved reference images to accelerate search-and-rescue.", table_cell_style),
            Paragraph("Chronological sighting trail with confidence score triage.", table_cell_style)
        ],
        [
            Paragraph("<b>3. Smart College Attendance</b>", table_cell_style),
            Paragraph("Simultaneously identify enrolled students, prevent proxy check-ins, eliminate duplicate entries, and export reports.", table_cell_style),
            Paragraph("Automated daily/subject-wise PDF & Excel ledgers.", table_cell_style)
        ],
        [
            Paragraph("<b>4. Workplace Access Management</b>", table_cell_style),
            Paragraph("Verify enrolled employees at turnstiles/doors, record ingress/egress, and flag unlisted or unauthorized personnel.", table_cell_style),
            Paragraph("Sub-second access verification and security alerts.", table_cell_style)
        ],
        [
            Paragraph("<b>5. Hospital & Patient Assistance</b>", table_cell_style),
            Paragraph("Identify registered patients in medical facilities who may become disoriented or wander into danger.", table_cell_style),
            Paragraph("Strict consent-based enrollment; silent nursing alerts.", table_cell_style)
        ],
        [
            Paragraph("<b>6. Transport Hub Security</b>", table_cell_style),
            Paragraph("Trace movement of persons of interest across airport terminals, railway platforms, and transit gates.", table_cell_style),
            Paragraph("Multi-camera spatial trajectory mapping under access controls.", table_cell_style)
        ],
        [
            Paragraph("<b>7. Public-Event Safety</b>", table_cell_style),
            Paragraph("Concert & festival safety: authorized POI review plus non-biometric crowd counting and density alerts.", table_cell_style),
            Paragraph("Anonymous crowd analytics; no profiling of general public.", table_cell_style)
        ],
        [
            Paragraph("<b>8. Elderly & Vulnerable Care</b>", table_cell_style),
            Paragraph("Assist caregivers in assisted living homes in locating registered residents who may wander away.", table_cell_style),
            Paragraph("Consent-governed resident safety and perimeter gate alerts.", table_cell_style)
        ],
        [
            Paragraph("<b>9. Retail & Facility Security</b>", table_cell_style),
            Paragraph("Deter repeat organized theft offenders, guard staff-only inventory zones, and greet opt-in VIP guests.", table_cell_style),
            Paragraph("Discrete security notifications; strict loss prevention limits.", table_cell_style)
        ],
        [
            Paragraph("<b>10. Real-Time Tracking & Analytics</b>", table_cell_style),
            Paragraph("Cross-camera re-identification (Re-ID), dwell time calculation, spatial heatmaps, and path reconstruction.", table_cell_style),
            Paragraph("Anonymized trajectory hashing; zero raw frame retention.", table_cell_style)
        ]
    ]

    sector_table = Table(sector_table_data, colWidths=[110, 244, 150])
    sector_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(sector_table)
    story.append(Spacer(1, 10))

    # ==========================
    # 3. SYSTEM ARCHITECTURE & PIPELINE
    # ==========================
    story.append(Paragraph("3. System Architecture & Technical Flow", h1_style))
    story.append(Paragraph(
        "FaceTrack AI implements a modular <b>Model-View-Controller (MVC)</b> architecture divided into four decoupled tiers:",
        body_style
    ))
    
    arch_data = [
        [Paragraph("Tier", table_header_style), Paragraph("Component", table_header_style), Paragraph("Key Responsibilities & Technologies", table_header_style)],
        [
            Paragraph("Presentation", table_cell_style),
            Paragraph("HTML5 / Canvas / WebRTC", table_cell_style),
            Paragraph("Captures live video feed (2-4 FPS), renders interactive HUD bounding boxes, coordinates voice speech alerts.", table_cell_style)
        ],
        [
            Paragraph("Application", table_cell_style),
            Paragraph("Flask Blueprints (`routes/`)", table_cell_style),
            Paragraph("Exposes REST JSON endpoints (`/api/recognize_frame`, `/api/upload_target`), handles session routing, and renders templates.", table_cell_style)
        ],
        [
            Paragraph("AI Engine", table_cell_style),
            Paragraph("`services/face_service.py`", table_cell_style),
            Paragraph("Frame decoding, face detection (HOG/Haar), 68-point landmarks, 128D embeddings, Euclidean vector matching, and liveness scoring.", table_cell_style)
        ],
        [
            Paragraph("Data Tier", table_cell_style),
            Paragraph("SQLite (`database.db`)", table_cell_style),
            Paragraph("Relational schema with foreign keys, storing target profiles, serialized JSON embeddings, detection audit logs, and settings.", table_cell_style)
        ]
    ]
    arch_table = Table(arch_data, colWidths=[70, 130, 304])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 10))

    # Callout Box: Frame Recognition Sequence
    callout_data = [[
        Paragraph(
            "<b>Data Flow Sequence:</b> Client WebRTC Video &rarr; Canvas Snapshot (Base64 JPEG) &rarr; "
            "HTTP POST to <code>/api/recognize_frame</code> &rarr; NumPy Buffer Decode &rarr; Face Bounding Box &rarr; "
            "128D Embedding Extraction &rarr; Vector Distance vs DB Encodings &rarr; Liveness/Emotion Math &rarr; "
            "JSON Response with Coordinates &rarr; Client Canvas Draws Green/Red Target Tag & Plays Audio.",
            callout_style
        )
    ]]
    callout_table = Table(callout_data, colWidths=[504])
    callout_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BOX_BG),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_ACCENT),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(callout_table)
    story.append(Spacer(1, 10))

    # ==========================
    # 4. COMPUTER VISION & AI/ML PIPELINE
    # ==========================
    story.append(Paragraph("4. Computer Vision & Mathematical Formulations", h1_style))
    story.append(Paragraph(
        "The biometrics pipeline operates on mathematically sound computer vision algorithms:",
        body_style
    ))

    story.append(Paragraph("4.1 128-Dimensional Deep Metric Embeddings & Vector Distance", h2_style))
    story.append(Paragraph(
        "A deep residual network (ResNet) projects the aligned face into a 128-dimensional Euclidean space where "
        "distances correspond to facial similarities. The similarity between a probe face embedding vector "
        "<i>e_probe</i> and a registered target embedding <i>e_known</i> is measured using Euclidean Distance (L2 norm):",
        body_style
    ))
    story.append(Paragraph(
        "<b>Distance Formula:</b> &nbsp;&nbsp; <code>d = &radic;(&sum;(e_known[i] - e_probe[i])&sup2;) &nbsp; for i &isin; [1, 128]</code>",
        code_style
    ))
    story.append(Paragraph(
        "The system uses a configurable tolerance threshold <b>&theta; = 0.50</b>. Matches with <code>d &le; &theta;</code> "
        "are accepted. The confidence percentage formula is derived as:",
        body_style
    ))
    story.append(Paragraph(
        "<b>Confidence Formula:</b> &nbsp;&nbsp; <code>Confidence (%) = 100.0 - (d / (2 &times; &theta;)) &times; 50.0</code> &nbsp; (clamped between 0.0% and 99.9%)",
        code_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("4.2 Liveness Verification & Anti-Spoofing Math", h2_style))
    story.append(Paragraph(
        "To prevent photo replay attacks and provide rich behavioral analytics, the system extracts 68 facial landmarks:",
        body_style
    ))
    story.append(Paragraph(
        "• <b>Eye Aspect Ratio (EAR) for Blink Detection:</b> Evaluates vertical eyelid distance over horizontal eye width:<br/>"
        "&nbsp;&nbsp;&nbsp;<code>EAR = (||p2 - p6|| + ||p3 - p5||) / (2.0 &times; ||p1 - p4||)</code><br/>"
        "&nbsp;&nbsp;&nbsp;If <code>EAR &lt; 0.22</code>, an active eye blink is logged, proving genuine biological presence.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Mouth Aspect Ratio (MAR) & Lip Corner Elevation:</b><br/>"
        "&nbsp;&nbsp;&nbsp;Calculates corner elevation <code>Lip_Center_Y - (Left_Corner_Y + Right_Corner_Y)/2</code>. "
        "A positive lift (&gt; 0.4px) or mouth width ratio (&gt; 0.38) triggers active smile detection.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Emotion Classification:</b> Evaluates inner eyebrow furrow ratio and eyebrow-to-eye vertical gaps to classify "
        "five distinct psychological states: <i>Happy, Surprised, Focused, Sad,</i> and <i>Neutral</i>.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Surgical Face Mask Detection:</b> Crops the lower 40% of the face, converts to HSV color space, checks for surgical "
        "blue hues (H &isin; [80, 130]), and tests grayscale standard deviation (&sigma; &lt; 18.0) to flag face coverings.",
        bullet_style
    ))
    story.append(Spacer(1, 10))

    # ==========================
    # 5. DATABASE SCHEMA
    # ==========================
    story.append(Paragraph("5. Database Schema & Data Models", h1_style))
    story.append(Paragraph(
        "The relational database (<code>database.db</code>) is managed through SQLite with foreign keys enforced and optimized indexes:",
        body_style
    ))

    db_data = [
        [Paragraph("Table Name", table_header_style), Paragraph("Primary Key", table_header_style), Paragraph("Key Fields & Constraints", table_header_style), Paragraph("Description", table_header_style)],
        [
            Paragraph("<b>targets</b>", table_cell_style),
            Paragraph("id (Auto)", table_cell_style),
            Paragraph("target_id (UNIQUE, TGT-XXXX), name, notes, photo_path, status, created_at", table_cell_style),
            Paragraph("Stores registered tracking identities and picture references.", table_cell_style)
        ],
        [
            Paragraph("<b>target_encodings</b>", table_cell_style),
            Paragraph("id (Auto)", table_cell_style),
            Paragraph("target_id (FK &rarr; targets), encoding_json (TEXT, 128 floats)", table_cell_style),
            Paragraph("Stores serialized 128-float face embeddings per target.", table_cell_style)
        ],
        [
            Paragraph("<b>detection_logs</b>", table_cell_style),
            Paragraph("id (Auto)", table_cell_style),
            Paragraph("target_id, target_name, timestamp, date, time, confidence, emotion, smile_detected, blink_detected, mask_detected, location_tag", table_cell_style),
            Paragraph("Audit trail of all face recognition events. Indexed on date and target_id.", table_cell_style)
        ],
        [
            Paragraph("<b>settings</b>", table_cell_style),
            Paragraph("key (TEXT)", table_cell_style),
            Paragraph("value (TEXT)", table_cell_style),
            Paragraph("System parameters: tolerance, audio_alert, cooldown_seconds.", table_cell_style)
        ],
        [
            Paragraph("<b>students</b>", table_cell_style),
            Paragraph("id (Auto)", table_cell_style),
            Paragraph("student_id (UNIQUE), name, roll_number, email, phone, department, semester", table_cell_style),
            Paragraph("Academic student registry for class attendance module.", table_cell_style)
        ],
        [
            Paragraph("<b>attendance</b>", table_cell_style),
            Paragraph("id (Auto)", table_cell_style),
            Paragraph("student_id, date, time, status (Present/Late), method, confidence", table_cell_style),
            Paragraph("Daily class attendance records and check-in times.", table_cell_style)
        ]
    ]
    db_table = Table(db_data, colWidths=[90, 60, 204, 150])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(db_table)
    story.append(Spacer(1, 10))

    # ==========================
    # 6. REST API SPECIFICATION
    # ==========================
    story.append(Paragraph("6. RESTful API Specification", h1_style))
    story.append(Paragraph(
        "FaceTrack AI exposes lightweight, high-speed JSON endpoints for frontend integration and third-party systems:",
        body_style
    ))

    api_data = [
        [Paragraph("Endpoint", table_header_style), Paragraph("Method", table_header_style), Paragraph("Payload Description", table_header_style), Paragraph("Response", table_header_style)],
        [
            Paragraph("<code>/api/recognize_frame</code>", table_cell_style),
            Paragraph("POST", table_cell_style),
            Paragraph("JSON: <code>{'image': 'data:image/jpeg;base64,...'}</code>", table_cell_style),
            Paragraph("JSON with matched targets, coordinates, confidence %, and liveness flags.", table_cell_style)
        ],
        [
            Paragraph("<code>/api/upload_target</code>", table_cell_style),
            Paragraph("POST", table_cell_style),
            Paragraph("Multipart form: <code>name</code>, <code>photo_file</code> OR base64 snapshot.", table_cell_style),
            Paragraph("Extracts encodings, generates ID (e.g. <code>TGT-8B3F11</code>), returns 200 OK.", table_cell_style)
        ],
        [
            Paragraph("<code>/api/stats</code>", table_cell_style),
            Paragraph("GET", table_cell_style),
            Paragraph("None", table_cell_style),
            Paragraph("Real-time counters: total targets, spotted today, last detection timestamp.", table_cell_style)
        ],
        [
            Paragraph("<code>/api/clear_logs</code>", table_cell_style),
            Paragraph("POST", table_cell_style),
            Paragraph("None", table_cell_style),
            Paragraph("Truncates detection history records.", table_cell_style)
        ]
    ]
    api_table = Table(api_data, colWidths=[120, 45, 179, 160])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 10))

    # ==========================
    # 7. UI/UX & INNOVATIONS
    # ==========================
    story.append(Paragraph("7. UI/UX & Engineering Highlights", h1_style))
    story.append(Paragraph(
        "• <b>Custom Glassmorphic Interface:</b> Styled with tailored HSL tokens, smooth dark theme backdrop, Outfit typography, "
        "and frosted glass cards (<code>backdrop-filter: blur(16px)</code>).",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Dynamic Canvas HUD:</b> Accurately overlays bounding boxes, identity tags, and status rings over the live WebRTC stream, "
        "automatically scaling between native camera resolutions (e.g., 1280x720) and browser display viewports.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Interactive Voice Alerts:</b> Leverages client-side Web Speech Synthesis (<code>speechSynthesis.speak</code>) to vocalize: "
        "<i>'Target Identified: [Name]'</i>, giving security operators eyes-free situational awareness.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Smart Anti-Flooding Cooldown:</b> Employs an in-memory timestamp hash combined with a SQL cooldown check (60s default) "
        "to prevent database record flooding when a person remains in camera view.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Automated Exporting Engine:</b> Compiles zebra-striped PDF incident summaries, detection audits, and ledgers "
        "via ReportLab and formatted Excel workbooks via OpenPyXL/Pandas with a single click.",
        bullet_style
    ))
    story.append(Paragraph(
        "• <b>Mobile Camera & Cross-Origin Support:</b> Includes pre-configured SSL certificates (<code>cert.pem</code>, <code>key.pem</code>) "
        "allowing smartphones on the same Wi-Fi network to grant WebRTC camera access over HTTPS.",
        bullet_style
    ))
    story.append(Spacer(1, 10))

    # ==========================
    # 8. HARDWARE & SOFTWARE SPECIFICATIONS
    # ==========================
    story.append(Paragraph("8. System Requirements & Tech Stack", h1_style))
    
    tech_data = [
        [Paragraph("Category", table_header_style), Paragraph("Minimum Requirement", table_header_style), Paragraph("Recommended Specification", table_header_style)],
        [
            Paragraph("Processor (CPU)", table_cell_style),
            Paragraph("Dual-Core 2.0 GHz Intel/AMD or Apple Silicon", table_cell_style),
            Paragraph("Quad-Core 2.5 GHz+ (Intel i5/i7/Apple M-series)", table_cell_style)
        ],
        [
            Paragraph("RAM", table_cell_style),
            Paragraph("4 GB DDR4", table_cell_style),
            Paragraph("8 GB+ DDR4 / Unified Memory", table_cell_style)
        ],
        [
            Paragraph("Camera Sensor", table_cell_style),
            Paragraph("720p HD Webcam (30 FPS)", table_cell_style),
            Paragraph("1080p Full HD Wide-Angle Camera", table_cell_style)
        ],
        [
            Paragraph("Operating System", table_cell_style),
            Paragraph("Linux (Ubuntu 20.04+), macOS 12+, Windows 10/11", table_cell_style),
            Paragraph("macOS Sonoma / Ubuntu 22.04 LTS", table_cell_style)
        ],
        [
            Paragraph("Python Environment", table_cell_style),
            Paragraph("Python 3.10+", table_cell_style),
            Paragraph("Python 3.11 / 3.12 with OpenCV & Dlib compiled", table_cell_style)
        ]
    ]
    tech_table = Table(tech_data, colWidths=[110, 194, 200])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, COLOR_BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 10))

    # ==========================
    # 9. FUTURE ENHANCEMENTS & CONCLUSION
    # ==========================
    story.append(Paragraph("9. Future Enhancements & Conclusion", h1_style))
    story.append(Paragraph(
        "<b>Future Scope:</b><br/>"
        "1. <b>Multi-Camera RTSP Streams:</b> Ingest continuous video feeds from multiple distributed IP security cameras.<br/>"
        "2. <b>GPU TensorRT Acceleration:</b> Deploy NVIDIA TensorRT for real-time batch processing of 30+ faces per frame at 60 FPS.<br/>"
        "3. <b>Active Liveness Challenges:</b> Introduce randomized prompts (e.g., 'Turn head 30&deg; right', 'Blink twice') for high-security areas.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Conclusion:</b><br/>"
        "FaceTrack AI demonstrates a robust, production-ready implementation of modern computer vision. By combining deep metric "
        "face embeddings, real-time liveness analysis, anti-flooding rate limiting, Human-in-the-Loop verification protocols, "
        "and an intuitive browser-based Glassmorphism UI, the project delivers a secure, touchless, and versatile biometric "
        "surveillance, tracking, and analytics platform across public safety, institutional, healthcare, transit, and enterprise operations.",
        body_style
    ))

    # Build PDF with dynamic numbering
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[SUCCESS] PDF generated successfully: {filename}")


if __name__ == '__main__':
    output_filename = "FaceTrack_AI_Project_Report.pdf"
    if len(sys.argv) > 1:
        output_filename = sys.argv[1]
    build_pdf(output_filename)
