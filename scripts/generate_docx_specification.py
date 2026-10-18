#!/usr/bin/env python3
"""
generate_docx_specification.py
Builds an executive-grade Microsoft Word (.docx) document detailing
all API endpoints, guest/public requests, authentication models, request/response
schemas, and frontend/external service integrations for the connectED platform.
"""

import os
import sys
import json
from datetime import datetime
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# --- Color Palette ---
COLOR_NAVY = RGBColor(30, 58, 138)       # #1E3A8A - Primary Header
COLOR_BLUE = RGBColor(37, 99, 235)       # #2563EB - Secondary Header / Accents
COLOR_DARK = RGBColor(15, 23, 42)        # #0F172A - Body Text
COLOR_MUTED = RGBColor(100, 116, 139)    # #64748B - Metadata / Subtitles
COLOR_GREEN = RGBColor(5, 150, 105)      # #059669 - Guest / Public Badge
COLOR_AMBER = RGBColor(217, 119, 6)      # #D97706 - Webhook / Warning Badge
COLOR_PURPLE = RGBColor(124, 58, 237)    # #7C3AED - Role Required Badge
COLOR_WHITE = RGBColor(255, 255, 255)

HEX_NAVY = "1E3A8A"
HEX_BLUE = "2563EB"
HEX_BLUE_BG = "EFF6FF"
HEX_GREEN_BG = "ECFDF5"
HEX_AMBER_BG = "FFFBEB"
HEX_PURPLE_BG = "F5F3FF"
HEX_GRAY_BG = "F8FAFC"
HEX_BORDER = "CBD5E1"
HEX_CODE_BG = "F1F5F9"

def set_cell_background(cell, hex_color):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def set_table_borders(table, border_color=HEX_BORDER):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="single" w:sz="6" w:space="0" w:color="{border_color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="{border_color}"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def format_cell_text(cell, text, bold=False, italic=False, font_size=9, color=COLOR_DARK, align=WD_ALIGN_PARAGRAPH.LEFT):
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.1
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(font_size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    return run

def add_header_p(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    h.paragraph_format.keep_with_next = True
    if level == 1:
        h.paragraph_format.space_before = Pt(20)
        h.paragraph_format.space_after = Pt(6)
        for run in h.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.color.rgb = COLOR_NAVY
    elif level == 2:
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
        for run in h.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(13)
            run.font.bold = True
            run.font.color.rgb = COLOR_BLUE
    elif level == 3:
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(2)
        for run in h.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(11)
            run.font.bold = True
            run.font.color.rgb = COLOR_NAVY
    return h

def add_paragraph_styled(doc, text, bold=False, italic=False, color=COLOR_DARK, space_after=4):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(10)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    return p

def add_callout(doc, text, title="NOTE", box_type="info"):
    bg_hex = HEX_BLUE_BG
    border_hex = "2563EB"
    title_rgb = COLOR_BLUE
    if box_type == "guest":
        bg_hex = HEX_GREEN_BG
        border_hex = "059669"
        title_rgb = COLOR_GREEN
    elif box_type == "warning":
        bg_hex = HEX_AMBER_BG
        border_hex = "D97706"
        title_rgb = COLOR_AMBER
    elif box_type == "purple":
        bg_hex = HEX_PURPLE_BG
        border_hex = "7C3AED"
        title_rgb = COLOR_PURPLE

    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.5)
    
    cell = table.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=120, bottom=120, left=160, right=160)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_hex}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r_title = p.add_run(f"[{title}] ")
    r_title.bold = True
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(9.5)
    r_title.font.color.rgb = title_rgb
    
    r_body = p.add_run(text)
    r_body.font.name = 'Calibri'
    r_body.font.size = Pt(9.5)
    r_body.font.color.rgb = COLOR_DARK
    
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(0)
    p_space.paragraph_format.space_after = Pt(4)

def add_code_block(doc, code_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.5)
    
    cell = table.cell(0, 0)
    set_cell_background(cell, HEX_CODE_BG)
    set_cell_margins(cell, top=90, bottom=90, left=140, right=140)
    
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        f'<w:left w:val="single" w:sz="16" w:space="0" w:color="94A3B8"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        f'<w:right w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(code_text.strip())
    run.font.name = 'Consolas'
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(30, 41, 59)
    
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(0)
    p_space.paragraph_format.space_after = Pt(4)

def style_header_row(row, titles, widths, align_list=None):
    for i, title in enumerate(titles):
        cell = row.cells[i]
        cell.width = widths[i]
        set_cell_background(cell, HEX_NAVY)
        set_cell_margins(cell, top=110, bottom=110, left=120, right=120)
        align = align_list[i] if align_list else WD_ALIGN_PARAGRAPH.LEFT
        format_cell_text(cell, title, bold=True, font_size=9, color=COLOR_WHITE, align=align)

def build_document():
    doc = docx.Document()
    
    # 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # =========================================================================
    # DOCUMENT COVER / TITLE HEADER
    # =========================================================================
    p_top = doc.add_paragraph()
    p_top.paragraph_format.space_before = Pt(12)
    p_top.paragraph_format.space_after = Pt(4)
    r_platform = p_top.add_run("CONNECT-ED PLATFORM ARCHITECTURE")
    r_platform.font.name = 'Calibri'
    r_platform.font.size = Pt(11)
    r_platform.bold = True
    r_platform.font.color.rgb = COLOR_BLUE

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(2)
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run("Comprehensive API Endpoints & Guest Requests Specification")
    r_title.font.name = 'Calibri'
    r_title.font.size = Pt(22)
    r_title.bold = True
    r_title.font.color.rgb = COLOR_NAVY

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run(
        "Complete technical catalog of all 29 REST API endpoints, guest-accessible routes, authentication models, "
        "request/response schemas, frontend client mappings, and external webhook integrations."
    )
    r_sub.font.name = 'Calibri'
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = COLOR_MUTED

    # Metadata Table
    meta_table = doc.add_table(rows=5, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    set_table_borders(meta_table)
    col_w = [Inches(2.2), Inches(4.3)]
    
    meta_data = [
        ("Platform Version", "connectED v1.0.0 (FastAPI + React 19 + MongoDB Atlas)"),
        ("Base API URL", "http://localhost:8000/api/v1 (Business Routes) | http://localhost:8000 (Health/Docs)"),
        ("Frontend Application", "http://localhost:5173 (Vite + React SPA)"),
        ("Authentication Types", "Public Guest, Bearer JWT, Role-Based Access Control (RBAC), Webhook Secret"),
        ("Documentation Date", datetime.now().strftime("%B %d, %Y")),
    ]
    for row_idx, (k, v) in enumerate(meta_data):
        row = meta_table.rows[row_idx]
        row.cells[0].width = col_w[0]
        row.cells[1].width = col_w[1]
        set_cell_background(row.cells[0], HEX_GRAY_BG)
        set_cell_margins(row.cells[0], top=80, bottom=80, left=120, right=120)
        set_cell_margins(row.cells[1], top=80, bottom=80, left=120, right=120)
        format_cell_text(row.cells[0], k, bold=True, font_size=9, color=COLOR_NAVY)
        format_cell_text(row.cells[1], v, bold=False, font_size=9, color=COLOR_DARK)

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # =========================================================================
    # SECTION 1: ARCHITECTURE OVERVIEW & REQUEST LIFECYCLE
    # =========================================================================
    add_header_p(doc, "1. Architecture Overview & Authentication Models", level=1)
    
    add_paragraph_styled(
        doc,
        "The connectED backend is built on a high-performance, asynchronous FastAPI framework that interacts "
        "with MongoDB Atlas. All API routes are strictly versioned under the `/api/v1` namespace, with the exception "
        "of system-level monitoring (`/health`) and API discovery (`/docs`, `/redoc`, `/openapi.json`)."
    )

    add_header_p(doc, "1.1 The Four Authentication Classes", level=2)
    add_paragraph_styled(
        doc,
        "Endpoints in connectED fall into one of four distinct security and authorization classes:"
    )

    auth_classes_table = doc.add_table(rows=5, cols=3)
    auth_classes_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    auth_classes_table.autofit = False
    set_table_borders(auth_classes_table)
    widths = [Inches(1.8), Inches(2.2), Inches(2.5)]
    style_header_row(auth_classes_table.rows[0], ["Auth Class", "Required Headers / Credentials", "Target Endpoints & Scope"], widths)

    classes_data = [
        ("Class 1: Public / Guest", "None (No authorization header required)", "Login, registration, health check, OpenAPI documentation. Fully accessible to unauthenticated guests and clients."),
        ("Class 2: Authenticated User", "Authorization: Bearer <JWT_TOKEN>", "Standard business operations: profiles, mentor search, mentorship requests, meetings, graph, communities."),
        ("Class 3: Role-Restricted (RBAC)", "Authorization: Bearer <JWT_TOKEN> + Matching Platform Role", "Targeted role actions: mentors responding to requests, student approving recommendations, recruiters posting opportunities."),
        ("Class 4: Webhook Signature", "X-Telegram-Bot-Api-Secret-Token: <SECRET>", "Inbound Telegram bot updates. Verified using constant-time cryptographic token comparison."),
    ]
    for row_idx, (col0, col1, col2) in enumerate(classes_data, start=1):
        row = auth_classes_table.rows[row_idx]
        bg = HEX_GRAY_BG if row_idx % 2 == 1 else "FFFFFF"
        for c_idx, text in enumerate([col0, col1, col2]):
            cell = row.cells[c_idx]
            cell.width = widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            format_cell_text(cell, text, bold=(c_idx==0), font_size=8.5, color=COLOR_NAVY if c_idx==0 else COLOR_DARK)

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    add_header_p(doc, "1.2 Standard Response & Error Envelope Protocol", level=2)
    add_paragraph_styled(
        doc,
        "All error responses produced by the connectED API strictly conform to a standardized error envelope, "
        "guaranteeing predictable error consumption for frontend and external callers:"
    )
    add_code_block(
        doc,
        """{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password.",
    "details": {}
  }
}"""
    )
    add_paragraph_styled(
        doc,
        "Standard HTTP status codes utilized across the API: "
        "200 OK (successful query/action), 201 Created (resource creation), 400 Bad Request (business rule violation), "
        "401 Unauthorized (missing or expired JWT token), 403 Forbidden (insufficient role privileges), "
        "404 Not Found (resource ID non-existent), 409 Conflict (duplicate unique constraint, e.g. email), "
        "and 422 Unprocessable Entity (Pydantic schema validation failure)."
    )

    # =========================================================================
    # SECTION 2: MASTER QUICK-REFERENCE MATRIX (ALL 29 ENDPOINTS)
    # =========================================================================
    add_header_p(doc, "2. Master API Endpoints Quick-Reference Matrix", level=1)
    add_paragraph_styled(
        doc,
        "The following matrix summarizes all 29 active endpoints across the connectED ecosystem. "
        "The 'Guest Request?' column explicitly highlights routes callable without an active session."
    )

    endpoints_master = [
        # System Health
        ("GET", "/health", "System Health", "Public Guest", "YES", "Direct HTTP"),
        ("GET", "/docs", "Documentation", "Public Guest", "YES", "Browser"),
        ("GET", "/openapi.json", "Documentation", "Public Guest", "YES", "Tooling"),
        # Authentication
        ("POST", "/api/v1/auth/login", "Authentication", "Public Guest", "YES", "api.login"),
        ("POST", "/api/v1/auth/register", "Authentication", "Public Guest", "YES", "api.register"),
        ("GET", "/api/v1/auth/me", "Authentication", "Bearer Auth", "NO", "api.getCurrentUser"),
        ("POST", "/api/v1/auth/logout", "Authentication", "Bearer Auth", "NO", "api.logout"),
        # Profiles
        ("GET", "/api/v1/profiles/me", "User Profiles", "Bearer Auth", "NO", "api.getMyProfile"),
        ("PATCH", "/api/v1/profiles/me", "User Profiles", "Bearer Auth", "NO", "api.updateMyProfile"),
        ("GET", "/api/v1/students/{user_id}", "User Profiles", "Bearer Auth", "NO", "api.getStudentProfile"),
        ("GET", "/api/v1/alumni/{user_id}", "User Profiles", "Bearer Auth", "NO", "api.getAlumniProfile"),
        ("GET", "/api/v1/alumni/{user_id}/verification", "User Profiles", "Bearer Auth", "NO", "Direct HTTP"),
        # Mentors
        ("GET", "/api/v1/mentors/recommendations", "AI Mentors", "Bearer (Student)", "NO", "api.getMentorRecommendations"),
        ("POST", "/api/v1/mentors/{mentor_id}/approve", "AI Mentors", "Bearer (Student)", "NO", "api.approveMentorRecommendation"),
        # Mentorship Requests
        ("POST", "/api/v1/mentorship-requests", "Mentorship", "Bearer (Student)", "NO", "api.createMentorshipRequest"),
        ("GET", "/api/v1/mentorship-requests", "Mentorship", "Bearer Auth", "NO", "api.getMentorshipRequests"),
        ("GET", "/api/v1/mentorship-requests/{request_id}", "Mentorship", "Bearer Auth", "NO", "api.getMentorshipRequest"),
        ("POST", "/api/v1/mentorship-requests/{request_id}/cancel", "Mentorship", "Bearer (Student)", "NO", "api.cancelMentorshipRequest"),
        ("POST", "/api/v1/mentorship-requests/{request_id}/respond", "Mentorship", "Bearer (Mentor)", "NO", "Direct HTTP / Bot"),
        # Meetings
        ("GET", "/api/v1/mentorship-requests/{id}/meeting-proposals", "Meetings", "Bearer Auth", "NO", "api.getMeetingProposals"),
        ("POST", "/api/v1/mentorship-requests/{id}/meeting-proposals", "Meetings", "Bearer Auth", "NO", "api.createMeetingProposal"),
        ("POST", "/api/v1/meeting-proposals/{id}/respond", "Meetings", "Bearer Auth", "NO", "api.respondToMeetingProposal"),
        # Telegram
        ("POST", "/api/v1/telegram/link/initiate", "Telegram Bot", "Bearer Auth", "NO", "Direct HTTP"),
        ("POST", "/api/v1/webhooks/telegram", "Telegram Bot", "Webhook Secret", "YES", "Telegram / n8n"),
        # Faculty & Research
        ("GET", "/api/v1/faculty/recommendations", "Faculty & Research", "Bearer (Student)", "NO", "api.getFacultyRecommendations"),
        ("GET", "/api/v1/research-projects", "Faculty & Research", "Bearer Auth", "NO", "api.getResearchProjects"),
        # Opportunities
        ("GET", "/api/v1/opportunities", "Opportunities", "Bearer Auth", "NO", "api.getOpportunities"),
        ("POST", "/api/v1/opportunities", "Opportunities", "Bearer (Recruiter+)", "NO", "Direct HTTP"),
        # Knowledge Graph
        ("GET", "/api/v1/graph/me", "Knowledge Graph", "Bearer Auth", "NO", "api.getKnowledgeGraph"),
        # Communities & Notifications
        ("GET", "/api/v1/communities", "Communities", "Bearer Auth", "NO", "api.getCommunities"),
        ("GET", "/api/v1/notifications", "Notifications", "Bearer Auth", "NO", "api.getNotifications"),
    ]

    matrix_table = doc.add_table(rows=len(endpoints_master) + 1, cols=6)
    matrix_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    matrix_table.autofit = False
    set_table_borders(matrix_table)
    m_widths = [Inches(0.7), Inches(2.2), Inches(1.3), Inches(1.0), Inches(0.6), Inches(0.7)]
    style_header_row(matrix_table.rows[0], ["Method", "Endpoint Path", "Category", "Access Level", "Guest?", "Frontend SDK"], m_widths)

    for idx, (method, path, cat, auth_lvl, is_guest, fe_sdk) in enumerate(endpoints_master, start=1):
        row = matrix_table.rows[idx]
        bg = HEX_GREEN_BG if is_guest == "YES" else (HEX_GRAY_BG if idx % 2 == 1 else "FFFFFF")
        
        # Color method badge
        m_color = COLOR_BLUE
        if method == "POST":
            m_color = COLOR_NAVY
        elif method == "PATCH":
            m_color = COLOR_AMBER
        
        for c_idx, val in enumerate([method, path, cat, auth_lvl, is_guest, fe_sdk]):
            cell = row.cells[c_idx]
            cell.width = m_widths[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            
            c_bold = (c_idx in [0, 4])
            text_color = COLOR_DARK
            if c_idx == 0:
                text_color = m_color
            elif c_idx == 4 and is_guest == "YES":
                text_color = COLOR_GREEN
            
            format_cell_text(cell, val, bold=c_bold, font_size=8, color=text_color)

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # =========================================================================
    # SECTION 3: DEDICATED SPOTLIGHT - PUBLIC & GUEST REQUEST ENDPOINTS
    # =========================================================================
    add_header_p(doc, "3. Dedicated Spotlight: All Public & Guest Request Endpoints", level=1)
    add_paragraph_styled(
        doc,
        "This section documents all endpoints that can be reached without an existing user session token "
        "('Guest Requests'). These endpoints are publicly accessible, require stringent input validation, "
        "and form the entry points for external visitors, unauthenticated users, and third-party webhooks."
    )

    add_callout(
        doc,
        "Public and guest endpoints operate without Bearer token headers. They employ rate-limiting, "
        "credential hashing, or cryptographic webhook token validation to prevent brute-force attacks and tampering.",
        title="SECURITY CRITICAL: GUEST ACCESS POLICIES",
        box_type="guest"
    )

    guest_endpoints = [
        {
            "title": "3.1 Infrastructure Health Check",
            "method": "GET",
            "path": "/health",
            "desc": "Publicly accessible endpoint utilized by load balancers, container orchestrators (Kubernetes/ECS), and uptime monitors to verify backend service liveness.",
            "auth": "None (Public Guest)",
            "params": "None",
            "req_body": "None",
            "response": """HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ok",
  "service": "connectED-backend",
  "version": "1.0.0"
}""",
            "fe_caller": "Monitoring tools, curl, automated heartbeat probes."
        },
        {
            "title": "3.2 User Authentication & JWT Issuance",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "desc": "Primary authentication gateway. Takes plain credentials, verifies the Argon2/Bcrypt hash against MongoDB Atlas, and returns a signed HS256 JWT access token along with the user's profile.",
            "auth": "None (Public Guest)",
            "params": "None",
            "req_body": """{
  "email": "aisha.student@university.edu",
  "password": "Demo1234!"
}""",
            "response": """HTTP/1.1 200 OK
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "671249b809a7b7a123456789",
    "email": "aisha.student@university.edu",
    "role": "student",
    "name": "Aisha Khan",
    "status": "active"
  }
}""",
            "fe_caller": "frontend/src/pages/LoginPage.tsx via api.login(email, password)"
        },
        {
            "title": "3.3 New User Account Registration",
            "method": "POST",
            "path": "/api/v1/auth/register",
            "desc": "Public endpoint allowing prospective students, alumni mentors, faculty, recruiters, and founders to register an account. Enforces unique email constraints and minimum 8-character password complexity.",
            "auth": "None (Public Guest)",
            "params": "None",
            "req_body": """{
  "email": "priya.nair@example.com",
  "password": "SecurePassword123!",
  "role": "alumni",
  "name": "Priya Nair",
  "headline": "Lead Systems Architect @ CloudScale",
  "institution": "Stanford University"
}""",
            "response": """HTTP/1.1 201 Created
Content-Type: application/json

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "671249d909a7b7a123456790",
    "email": "priya.nair@example.com",
    "role": "alumni",
    "name": "Priya Nair",
    "status": "active"
  }
}""",
            "fe_caller": "frontend/src/pages/SignupPage.tsx via api.register(input)"
        },
        {
            "title": "3.4 External Telegram Bot Inbound Webhook",
            "method": "POST",
            "path": "/api/v1/webhooks/telegram",
            "desc": "Guest webhook receiver for incoming Telegram updates from Telegram servers or n8n workflow triggers. Validates identity via the X-Telegram-Bot-Api-Secret-Token HTTP header. Supports bot linking commands and mentor accept/decline inline button callbacks.",
            "auth": "Secret Header: X-Telegram-Bot-Api-Secret-Token",
            "params": "Header: X-Telegram-Bot-Api-Secret-Token (Required in production)",
            "req_body": """{
  "update_id": 10001,
  "message": {
    "message_id": 42,
    "from": {
      "id": 987654321,
      "first_name": "Alex",
      "username": "alex_johnson"
    },
    "chat": {
      "id": 987654321,
      "type": "private"
    },
    "text": "/start link_sec_ab12cd34ef56"
  }
}""",
            "response": """HTTP/1.1 200 OK
Content-Type: application/json

{
  "ok": true,
  "handled": "account_linked",
  "user_id": "671249c509a7b7a123456788"
}""",
            "fe_caller": "External Telegram Bot Servers / n8n Workflow Automation Engine"
        },
        {
            "title": "3.5 Interactive API Discovery Documentation (Swagger UI & OpenAPI)",
            "method": "GET",
            "path": "/docs | /redoc | /openapi.json",
            "desc": "OpenAPI 3.1 contract and interactive documentation interfaces for engineers, QA testers, and automated client generators.",
            "auth": "None (Public Guest)",
            "params": "None",
            "req_body": "None",
            "response": """HTTP/1.1 200 OK
Content-Type: text/html / application/json

Interactive Swagger UI / ReDoc HTML or raw OpenAPI 3.1 JSON definition.""",
            "fe_caller": "Direct web browser access, Swagger Inspector, Postman"
        }
    ]

    for g in guest_endpoints:
        add_header_p(doc, g["title"], level=2)
        add_paragraph_styled(doc, g["desc"])
        
        # Details table
        g_table = doc.add_table(rows=4, cols=2)
        g_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        g_table.autofit = False
        set_table_borders(g_table)
        g_widths = [Inches(1.8), Inches(4.7)]
        
        g_rows = [
            ("HTTP Method & Route", f"{g['method']} {g['path']}"),
            ("Authorization Level", g["auth"]),
            ("Request Parameters", g["params"]),
            ("Consumer / Caller", g["fe_caller"]),
        ]
        for r_i, (k_val, v_val) in enumerate(g_rows):
            r = g_table.rows[r_i]
            r.cells[0].width = g_widths[0]
            r.cells[1].width = g_widths[1]
            set_cell_background(r.cells[0], HEX_GRAY_BG)
            set_cell_margins(r.cells[0], top=60, bottom=60, left=100, right=100)
            set_cell_margins(r.cells[1], top=60, bottom=60, left=100, right=100)
            format_cell_text(r.cells[0], k_val, bold=True, font_size=8.5, color=COLOR_NAVY)
            format_cell_text(r.cells[1], v_val, bold=False, font_size=8.5, color=COLOR_DARK)
        
        if g["req_body"] != "None":
            add_paragraph_styled(doc, "Sample Request Payload (JSON):", bold=True, space_after=2)
            add_code_block(doc, g["req_body"])
        
        add_paragraph_styled(doc, "Sample Response Payload (JSON):", bold=True, space_after=2)
        add_code_block(doc, g["response"])

    # =========================================================================
    # SECTION 4: DETAILED ENDPOINT CATALOG (BY FUNCTIONAL MODULE)
    # =========================================================================
    add_header_p(doc, "4. Comprehensive Endpoint Catalog by Module", level=1)

    modules_data = [
        {
            "name": "4.1 Authentication & Session Management",
            "desc": "Handles login, registration, token identity validation, and logout invalidation.",
            "endpoints": [
                {
                    "method": "POST",
                    "path": "/api/v1/auth/login",
                    "summary": "User Login",
                    "access": "Public Guest",
                    "body": "UserLoginRequest (email: str, password: str)",
                    "resp": "TokenResponse (access_token, token_type: bearer, expires_in: int, user: CurrentUser)",
                    "fe": "api.login() -> LoginPage.tsx"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/auth/register",
                    "summary": "User Registration",
                    "access": "Public Guest",
                    "body": "UserRegisterRequest (email, password [>=8], role [student/alumni/faculty/recruiter/founder], name, headline?, institution?)",
                    "resp": "TokenResponse (access_token, token_type: bearer, expires_in: int, user: CurrentUser) [HTTP 201]",
                    "fe": "api.register() -> SignupPage.tsx"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/auth/me",
                    "summary": "Get Current User Identity",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None",
                    "resp": "CurrentUser (id, email, role, name, status)",
                    "fe": "api.getCurrentUser() -> RequireAuth.tsx & TopNav.tsx"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/auth/logout",
                    "summary": "Logout & Invalidate Token",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (uses Authorization header)",
                    "resp": "{ success: true, message: 'Logged out successfully' }",
                    "fe": "api.logout() -> UserMenu dropdown"
                }
            ]
        },
        {
            "name": "4.2 User Profiles & Directory Verification",
            "desc": "Manages user identity records, profile customization, and verified alumni badges.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/v1/profiles/me",
                    "summary": "Get Authenticated User Profile",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None",
                    "resp": "ProfileMe (id, user_id, headline, institution, department, current_organization, current_role, skills: list[str], career_goals: list[str], bio, visibility)",
                    "fe": "api.getMyProfile() -> ProfilePage.tsx & DashboardPage.tsx"
                },
                {
                    "method": "PATCH",
                    "path": "/api/v1/profiles/me",
                    "summary": "Update User Profile Details",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "ProfilePatchRequest (partial fields: headline, institution, skills, current_organization, bio, visibility, etc.)",
                    "resp": "ProfileMe (updated profile object)",
                    "fe": "api.updateMyProfile() -> ProfileEditModal.tsx"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/students/{user_id}",
                    "summary": "View Student Public Profile",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Path param: user_id)",
                    "resp": "StudentProfile (user_id, name, headline, institution, department, skills, career_goals, visible_status)",
                    "fe": "Student directory & mentor preview cards"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/alumni/{user_id}",
                    "summary": "View Alumni Mentor Profile",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Path param: user_id)",
                    "resp": "AlumniProfile (user_id, name, current_organization, current_role, graduation_year, skills, verified, freshness_score)",
                    "fe": "api.getAlumniProfile() -> MentorProfileView.tsx"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/alumni/{user_id}/verification",
                    "summary": "Get Alumni Verification Badge",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Path param: user_id)",
                    "resp": "{ user_id: str, verified: bool, verification_source: 'university_records' | 'linkedin_oauth', freshness_score: float }",
                    "fe": "Verified badge rendering in Mentor Card"
                }
            ]
        },
        {
            "name": "4.3 AI Mentor Matching & Explicit Approvals",
            "desc": "Semantic search engine matching students with alumni mentors using embeddings, requiring explicit user approval before request submission.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/v1/mentors/recommendations",
                    "summary": "Get Ranked Mentor Recommendations",
                    "access": "Student Role (Bearer JWT)",
                    "body": "None (Query params: limit=10, offset=0, skill: str, career_goal: str)",
                    "resp": "MentorRecommendationsResponse (items: list[MentorRecommendation], total: int, embedding_mode: 'minilm' | 'hash')",
                    "fe": "api.getMentorRecommendations() -> MentorsPage.tsx"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/mentors/{mentor_id}/approve",
                    "summary": "Approve Mentor Recommendation",
                    "access": "Student Role (Bearer JWT)",
                    "body": "None (Path param: mentor_id). Creates 60-minute valid single-use approval ticket.",
                    "resp": "{ mentor_id: str, approved: true, expires_at: '2026-10-18T08:30:00Z', message: 'Mentor recommendation approved.' }",
                    "fe": "api.approveMentorRecommendation() -> MentorsPage.tsx 'Approve & Request' flow"
                }
            ]
        },
        {
            "name": "4.4 Mentorship Requests & 48-Hour Deadline System",
            "desc": "Governs the formal mentorship request lifecycle, enforcing a strict backend-authoritative 48-hour response deadline.",
            "endpoints": [
                {
                    "method": "POST",
                    "path": "/api/v1/mentorship-requests",
                    "summary": "Create Mentorship Request",
                    "access": "Student Role (Bearer JWT) with Active Approval",
                    "body": "MentorshipRequestCreate (mentor_id: str, message: str)",
                    "resp": "MentorshipRequest (id, student_id, mentor_id, status: 'pending', response_deadline: 'ISO_TIMESTAMP + 48h', created_at) [HTTP 201]",
                    "fe": "api.createMentorshipRequest() -> RequestMentorshipModal.tsx"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/mentorship-requests",
                    "summary": "List User Mentorship Requests",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Query params: status='pending'|'accepted'|'declined'|'expired', limit=20, offset=0)",
                    "resp": "MentorshipRequestListResponse (items: list[MentorshipRequest], total: int)",
                    "fe": "api.getMentorshipRequests() -> DashboardPage.tsx & RequestsTab.tsx"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/mentorship-requests/{request_id}",
                    "summary": "Get Request Details",
                    "access": "Authenticated User (Student or Mentor participant)",
                    "body": "None (Path param: request_id)",
                    "resp": "MentorshipRequest detail with audit timestamps and deadline status",
                    "fe": "api.getMentorshipRequest() -> MentorshipDetailModal.tsx"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/mentorship-requests/{request_id}/cancel",
                    "summary": "Cancel Pending Request",
                    "access": "Student Owner (Bearer JWT)",
                    "body": "None (Path param: request_id)",
                    "resp": "{ id: str, status: 'cancelled', message: 'Mentorship request cancelled successfully.', updated_at: str }",
                    "fe": "api.cancelMentorshipRequest() -> RequestsTab.tsx"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/mentorship-requests/{request_id}/respond",
                    "summary": "Mentor Accept or Decline Response",
                    "access": "Target Mentor (Bearer JWT) or Telegram Webhook Callback",
                    "body": "{ action: 'accept' | 'decline', response_note?: str }",
                    "resp": "MentorshipRequest (status updated to 'accepted' or 'declined', updated_at: str)",
                    "fe": "Mentor Inbox / Telegram Bot inline reply"
                }
            ]
        },
        {
            "name": "4.5 Meeting Coordination & Mutual Agreement",
            "desc": "Coordinates meeting times for accepted mentorship relationships, ensuring meetings confirm only upon mutual consent.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/v1/mentorship-requests/{request_id}/meeting-proposals",
                    "summary": "List Meeting Proposals",
                    "access": "Student or Mentor participant (Bearer JWT)",
                    "body": "None (Path param: request_id)",
                    "resp": "{ items: list[MeetingProposal], total: int }",
                    "fe": "api.getMeetingProposals() -> MeetingScheduler.tsx"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/mentorship-requests/{request_id}/meeting-proposals",
                    "summary": "Propose Meeting Slot",
                    "access": "Participant (Bearer JWT)",
                    "body": "MeetingProposalCreate (proposed_time: ISO_STR, timezone_str: 'Asia/Kolkata' | 'America/New_York', note?: str)",
                    "resp": "MeetingProposal (id, request_id, proposed_by, proposed_time, status: 'proposed', responses: {}) [HTTP 201]",
                    "fe": "api.createMeetingProposal() -> ProposeMeetingModal.tsx"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/meeting-proposals/{proposal_id}/respond",
                    "summary": "Respond to Meeting Proposal",
                    "access": "Counterpart Participant (Bearer JWT)",
                    "body": "MeetingProposalRespond (action: 'accept' | 'decline', note?: str)",
                    "resp": "MeetingProposal (status: 'confirmed' if mutually agreed, or 'declined')",
                    "fe": "api.respondToMeetingProposal() -> MeetingScheduler.tsx"
                }
            ]
        },
        {
            "name": "4.6 Telegram Bot Deep Linking & Outbox Integration",
            "desc": "Seamless notification system linking Telegram users to mentorship workflows without exposing database secrets.",
            "endpoints": [
                {
                    "method": "POST",
                    "path": "/api/v1/telegram/link/initiate",
                    "summary": "Initiate Telegram Account Link",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None",
                    "resp": "{ token: 'link_sec_...', deep_link: 'https://t.me/connectED_bot?start=link_sec_...', expires_at: str }",
                    "fe": "Settings / Notification Preferences 'Connect Telegram' button"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/webhooks/telegram",
                    "summary": "Process Inbound Bot Updates",
                    "access": "Webhook Secret (X-Telegram-Bot-Api-Secret-Token) [GUEST]",
                    "body": "TelegramWebhookUpdate (update_id: int, message?: TelegramMessage, callback_query?: TelegramCallbackQuery)",
                    "resp": "{ ok: true, handled: 'account_linked' | 'mentorship_accepted' | 'mentorship_declined' }",
                    "fe": "Telegram Cloud Bot Service & n8n Automation Workflows"
                }
            ]
        },
        {
            "name": "4.7 Faculty Discovery & Academic Research",
            "desc": "Enables students to discover faculty research labs, grants, and co-authorship opportunities.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/v1/faculty/recommendations",
                    "summary": "Get Faculty Recommendations",
                    "access": "Student Role (Bearer JWT)",
                    "body": "None (Query params: limit=10, offset=0)",
                    "resp": "FacultyRecommendationsResponse (items: list[FacultyRecommendation], total: int)",
                    "fe": "api.getFacultyRecommendations() -> FacultyPage.tsx"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/research-projects",
                    "summary": "List Active Research Projects",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Query params: research_area?: str, limit=20, offset=0)",
                    "resp": "{ items: list[ResearchProject], total: int, limit: int, offset: int }",
                    "fe": "api.getResearchProjects() -> ResearchExplorePage.tsx"
                }
            ]
        },
        {
            "name": "4.8 Opportunities, Jobs & Internships",
            "desc": "Marketplace for professional roles posted by alumni, recruiters, and startup founders.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/v1/opportunities",
                    "summary": "Browse Opportunities",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Query params: type='job'|'internship'|'collaboration'|'cofounder', limit=20, offset=0)",
                    "resp": "{ items: list[Opportunity], total: int, limit: int, offset: int }",
                    "fe": "api.getOpportunities() -> OpportunitiesPage.tsx"
                },
                {
                    "method": "POST",
                    "path": "/api/v1/opportunities",
                    "summary": "Post New Opportunity",
                    "access": "Recruiter / Founder / Faculty / Alumni Role (Bearer JWT)",
                    "body": "OpportunityCreate (type: str, title: str, description: str, organization: str, location?: str, required_skills: list[str], deadline?: str, application_url?: str, contact_email?: str)",
                    "resp": "Opportunity (id, title, creator_id, created_at) [HTTP 201]",
                    "fe": "PostJobModal.tsx -> Direct HTTP"
                }
            ]
        },
        {
            "name": "4.9 Professional Knowledge Graph & Communities",
            "desc": "Interactive multi-dimensional graph of skills, companies, alumni, and campus community boards.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/v1/graph/me",
                    "summary": "Get User Knowledge Graph",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Query params: depth=2, max_nodes=50)",
                    "resp": "KnowledgeGraphResponse (nodes: list[GraphNode], links: list[GraphEdge], root_user_id: str)",
                    "fe": "api.getKnowledgeGraph() -> KnowledgeGraphView.tsx"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/communities",
                    "summary": "List Campus Communities",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Query params: limit=20, offset=0)",
                    "resp": "{ items: list[Community], total: int, limit: int, offset: int }",
                    "fe": "api.getCommunities() -> CommunitiesPage.tsx"
                },
                {
                    "method": "GET",
                    "path": "/api/v1/notifications",
                    "summary": "List User Notifications",
                    "access": "Authenticated User (Bearer JWT)",
                    "body": "None (Query params: limit=20, offset=0)",
                    "resp": "{ items: list[Notification], total: int, limit: int, offset: int }",
                    "fe": "api.getNotifications() -> NotificationsDropdown.tsx"
                }
            ]
        }
    ]

    for mod in modules_data:
        add_header_p(doc, mod["name"], level=2)
        add_paragraph_styled(doc, mod["desc"])

        table = doc.add_table(rows=len(mod["endpoints"]) + 1, cols=5)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        set_table_borders(table)
        t_widths = [Inches(0.8), Inches(2.1), Inches(1.2), Inches(1.2), Inches(1.2)]
        style_header_row(table.rows[0], ["Method", "Path", "Access Level", "Payload / Body", "Frontend SDK Consumer"], t_widths)

        for e_idx, ep in enumerate(mod["endpoints"], start=1):
            row = table.rows[e_idx]
            bg = HEX_GREEN_BG if "Public Guest" in ep["access"] or "Webhook" in ep["access"] else (HEX_GRAY_BG if e_idx % 2 == 1 else "FFFFFF")
            
            m_col = COLOR_BLUE if ep["method"] == "GET" else (COLOR_NAVY if ep["method"] == "POST" else COLOR_AMBER)
            
            for c_i, val in enumerate([ep["method"], ep["path"], ep["access"], ep["body"], ep["fe"]]):
                cell = row.cells[c_i]
                cell.width = t_widths[c_i]
                set_cell_background(cell, bg)
                set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
                
                txt_color = m_col if c_i == 0 else COLOR_DARK
                format_cell_text(cell, val, bold=(c_i in [0, 2]), font_size=8, color=txt_color)
        
        doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # =========================================================================
    # SECTION 5: FRONTEND SDK METHOD MAPPING (api.ts)
    # =========================================================================
    add_header_p(doc, "5. Frontend Client SDK Reference (frontend/src/services/api.ts)", level=1)
    add_paragraph_styled(
        doc,
        "The React 19 frontend consumes backend endpoints through the strongly-typed `api` singleton "
        "defined in `frontend/src/services/api.ts`. The table below outlines all SDK methods, "
        "their underlying HTTP requests, and the frontend pages that invoke them."
    )

    sdk_methods = [
        ("api.login(email, pass)", "POST", "/api/v1/auth/login", "Public Guest", "LoginPage.tsx"),
        ("api.register(input)", "POST", "/api/v1/auth/register", "Public Guest", "SignupPage.tsx"),
        ("api.getCurrentUser()", "GET", "/api/v1/auth/me", "Bearer Auth", "RequireAuth.tsx, TopNav.tsx"),
        ("api.logout()", "POST", "/api/v1/auth/logout", "Bearer Auth", "UserDropdown.tsx"),
        ("api.getMyProfile()", "GET", "/api/v1/profiles/me", "Bearer Auth", "ProfilePage.tsx, DashboardPage.tsx"),
        ("api.updateMyProfile(data)", "PATCH", "/api/v1/profiles/me", "Bearer Auth", "EditProfileModal.tsx"),
        ("api.getAlumniProfile(id)", "GET", "/api/v1/alumni/{id}", "Bearer Auth", "MentorDetailModal.tsx"),
        ("api.getMentorRecommendations(f)", "GET", "/api/v1/mentors/recommendations", "Bearer (Student)", "MentorsPage.tsx"),
        ("api.approveMentorRecommendation(id)", "POST", "/api/v1/mentors/{id}/approve", "Bearer (Student)", "MentorsPage.tsx"),
        ("api.getMentorshipRequests(f)", "GET", "/api/v1/mentorship-requests", "Bearer Auth", "DashboardPage.tsx, RequestsTab.tsx"),
        ("api.createMentorshipRequest(data)", "POST", "/api/v1/mentorship-requests", "Bearer (Student)", "RequestMentorshipModal.tsx"),
        ("api.getMentorshipRequest(id)", "GET", "/api/v1/mentorship-requests/{id}", "Bearer Auth", "RequestDetailsModal.tsx"),
        ("api.cancelMentorshipRequest(id)", "POST", "/api/v1/mentorship-requests/{id}/cancel", "Bearer (Student)", "RequestsTab.tsx"),
        ("api.getMeetingProposals(reqId)", "GET", "/api/v1/mentorship-requests/{id}/meeting-proposals", "Bearer Auth", "MeetingScheduler.tsx"),
        ("api.createMeetingProposal(id, d)", "POST", "/api/v1/mentorship-requests/{id}/meeting-proposals", "Bearer Auth", "ProposeMeetingModal.tsx"),
        ("api.respondToMeetingProposal(id, a)", "POST", "/api/v1/meeting-proposals/{id}/respond", "Bearer Auth", "MeetingProposalCard.tsx"),
        ("api.getOpportunities(filters)", "GET", "/api/v1/opportunities", "Bearer Auth", "OpportunitiesPage.tsx"),
        ("api.getResearchProjects(filters)", "GET", "/api/v1/research-projects", "Bearer Auth", "ResearchPage.tsx"),
        ("api.getFacultyRecommendations()", "GET", "/api/v1/faculty/recommendations", "Bearer (Student)", "FacultyPage.tsx"),
        ("api.getKnowledgeGraph()", "GET", "/api/v1/graph/me", "Bearer Auth", "KnowledgeGraphPage.tsx"),
        ("api.getCommunities(filters)", "GET", "/api/v1/communities", "Bearer Auth", "CommunitiesPage.tsx"),
        ("api.getNotifications(filters)", "GET", "/api/v1/notifications", "Bearer Auth", "NotificationsBell.tsx"),
    ]

    sdk_table = doc.add_table(rows=len(sdk_methods) + 1, cols=5)
    sdk_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    sdk_table.autofit = False
    set_table_borders(sdk_table)
    sdk_widths = [Inches(2.1), Inches(0.7), Inches(1.8), Inches(0.9), Inches(1.0)]
    style_header_row(sdk_table.rows[0], ["SDK Method Signature", "Verb", "Target Endpoint", "Auth Level", "Primary UI Consumer"], sdk_widths)

    for s_idx, (method_sig, verb, ep_path, a_lvl, ui_page) in enumerate(sdk_methods, start=1):
        row = sdk_table.rows[s_idx]
        bg = HEX_GREEN_BG if "Public Guest" in a_lvl else (HEX_GRAY_BG if s_idx % 2 == 1 else "FFFFFF")
        for c_i, val in enumerate([method_sig, verb, ep_path, a_lvl, ui_page]):
            cell = row.cells[c_i]
            cell.width = sdk_widths[c_i]
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=80, right=80)
            format_cell_text(cell, val, bold=(c_i in [0, 3]), font_size=8, color=COLOR_DARK)

    doc.add_paragraph().paragraph_format.space_after = Pt(14)

    # =========================================================================
    # SECTION 6: EXTERNAL SERVICES & BACKGROUND WORKERS
    # =========================================================================
    add_header_p(doc, "6. External Services, Webhooks & Automated Workflows", level=1)
    add_paragraph_styled(
        doc,
        "connectED integrates with several external platforms and asynchronous background processes:"
    )

    add_header_p(doc, "6.1 Telegram Bot Integration & Outbox Delivery", level=2)
    add_paragraph_styled(
        doc,
        "Mentors receive instant Telegram alerts when a new mentorship request is submitted. "
        "The alert includes inline buttons ('Accept' / 'Decline') that post callback queries to "
        "`POST /api/v1/webhooks/telegram`. The backend utilizes a transactional Outbox pattern to deliver "
        "messages reliably without blocking FastAPI request workers or risking data loss during network hiccups."
    )

    add_header_p(doc, "6.2 n8n Automation Workflows", level=2)
    add_paragraph_styled(
        doc,
        "The project includes pre-configured n8n workflow definitions (located in the project root file `n8n`). "
        "These workflows listen for Telegram triggers, execute automated enrichment flows, and relay status "
        "updates to connectED webhook listeners securely using secret authorization headers."
    )

    add_header_p(doc, "6.3 48-Hour Deadline Expiration Background Worker", level=2)
    add_paragraph_styled(
        doc,
        "During FastAPI lifespan startup, the background task `start_expiration_worker(poll_interval_seconds=60)` "
        "is initiated. Every 60 seconds, it sweeps the MongoDB database for any pending mentorship requests whose "
        "`response_deadline` has lapsed. It automatically transitions expired requests to status `'expired'`, "
        "releasing the student to explore alternate mentors without indefinite stalls."
    )

    # Save Document
    target_path = "/Users/apple/Desktop/Temp/connectED_API_Endpoints_Specification.docx"
    doc.save(target_path)
    print(f"Document successfully created at: {target_path}")
    print(f"File size: {os.path.getsize(target_path):,} bytes")

if __name__ == "__main__":
    build_document()
