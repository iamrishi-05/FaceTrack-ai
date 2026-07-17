import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from utils.logger import log_event

class ReportService:
    @staticmethod
    def generate_excel(records):
        """
        Generates an Excel workbook file stream using Pandas and OpenPyXL.
        Format column spacing and aesthetics before outputting bytes.
        """
        # Convert sqlite3.Row elements to dictionaries
        data = []
        for r in records:
            data.append({
                'Student ID': r['student_id'],
                'Name': r['name'],
                'Roll Number': r['roll_number'],
                'Department': r['department'],
                'Semester': r['semester'],
                'Check-in Date': r['date'],
                'Check-in Time': r['time'],
                'Status': r['status'],
                'Method': r['method'],
                'Confidence %': r['confidence'] if r['confidence'] else 'N/A',
                'Emotion': r['emotion'].capitalize() if r['emotion'] else 'N/A'
            })
            
        df = pd.DataFrame(data)
        
        # Write to Bytes buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Attendance Logs', index=False)
            
            # Stylize column widths using openpyxl
            workbook = writer.book
            worksheet = writer.sheets['Attendance Logs']
            
            # Set grid styles and fit columns to maximum length
            for col in worksheet.columns:
                max_len = max(len(str(cell.value or '')) for cell in col)
                col_letter = col[0].column_letter
                worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)
                
        output.seek(0)
        log_event("INFO", "Reporting", f"Excel workbook report compiled with {len(records)} entries.")
        return output.getvalue()

    @staticmethod
    def generate_pdf(records, filter_description="All Records"):
        """
        Generates a premium PDF document using ReportLab.
        Draws branded headers, zebra-striped tables, and metadata details.
        """
        output = io.BytesIO()
        doc = SimpleDocTemplate(
            output,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # 1. Branded Headers
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            textColor=colors.HexColor('#002b49'), # Premium navy blue
            spaceAfter=6
        )
        sub_style = ParagraphStyle(
            'ReportSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=20
        )
        
        story.append(Paragraph("FaceTrack AI – Attendance Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Filters: {filter_description}", sub_style))
        
        header_style = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.white
        )

        # 2. Build logs table
        # Table columns: ID, Name, Roll, Dept, Date, Time, Status
        table_data = [[
            Paragraph("Student ID", header_style),
            Paragraph("Name", header_style),
            Paragraph("Roll", header_style),
            Paragraph("Department", header_style),
            Paragraph("Date", header_style),
            Paragraph("Time", header_style),
            Paragraph("Status", header_style)
        ]]
        
        for r in records:
            # Wrap in Paragraphs to support auto word-wrapping in ReportLab cells
            table_data.append([
                Paragraph(r['student_id'], styles['Normal']),
                Paragraph(r['name'], styles['Normal']),
                Paragraph(r['roll_number'], styles['Normal']),
                Paragraph(r['department'], styles['Normal']),
                Paragraph(r['date'], styles['Normal']),
                Paragraph(r['time'], styles['Normal']),
                Paragraph(f"<b>{r['status']}</b>", styles['Normal'])
            ])
            
        # Table formatting configurations
        # Letter width = 612. Margins = 36 * 2. Printable width = 540
        # Columns widths: ID(85), Name(105), Roll(45), Dept(115), Date(65), Time(60), Status(65) = 540
        col_widths = [85, 105, 45, 115, 65, 60, 65]
        
        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        t_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')), # Dark header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Apply zebra striping colors
        for idx in range(1, len(table_data)):
            bg_color = colors.HexColor('#f8fafc') if idx % 2 == 0 else colors.HexColor('#ffffff')
            t_style.add('BACKGROUND', (0, idx), (-1, idx), bg_color)
            
            # Apply colored text to status
            status_cell = table_data[idx][6].text
            if "Present" in status_cell:
                t_style.add('TEXTCOLOR', (6, idx), (6, idx), colors.HexColor('#10b981')) # green
            elif "Late" in status_cell:
                t_style.add('TEXTCOLOR', (6, idx), (6, idx), colors.HexColor('#d97706')) # orange
            else:
                t_style.add('TEXTCOLOR', (6, idx), (6, idx), colors.HexColor('#ef4444')) # red
                
        t.setStyle(t_style)
        story.append(t)
        
        # Build Document
        doc.build(story)
        output.seek(0)
        log_event("INFO", "Reporting", f"PDF report document compiled with {len(records)} entries.")
        return output.getvalue()
