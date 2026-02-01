"""
PDF Report Generation Service
Generates professional medical-style genetic analysis reports using ReportLab
"""
import os
import json
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image, PageBreak, HRFlowable, KeepTogether
)
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.piecharts import Pie

# Population descriptions
POPULATION_INFO = {
    "CEU": {"name": "European (CEU)", "description": "Utah Residents with Northern and Western European Ancestry", "region": "Europe"},
    "YRI": {"name": "African (YRI)", "description": "Yoruba in Ibadan, Nigeria", "region": "Africa"},
    "JPT": {"name": "Japanese (JPT)", "description": "Japanese in Tokyo, Japan", "region": "East Asia"},
    "CHB": {"name": "Chinese (CHB)", "description": "Han Chinese in Beijing, China", "region": "East Asia"},
    "GIH": {"name": "South Asian (GIH)", "description": "Gujarati Indians in Houston, Texas", "region": "South Asia"},
    "ASW": {"name": "African American (ASW)", "description": "African Ancestry in Southwest USA", "region": "Americas"},
    "MXL": {"name": "Mexican (MXL)", "description": "Mexican Ancestry in Los Angeles, California", "region": "Americas"},
    "TSI": {"name": "Italian (TSI)", "description": "Toscani in Italia", "region": "Europe"},
    "LWK": {"name": "African (LWK)", "description": "Luhya in Webuye, Kenya", "region": "Africa"},
    "CHD": {"name": "Chinese American (CHD)", "description": "Chinese in Metropolitan Denver, Colorado", "region": "Americas"},
    "MKK": {"name": "African (MKK)", "description": "Maasai in Kinyawa, Kenya", "region": "Africa"},
}


class MedicalReportPDF:
    """Generate professional medical-style PDF reports for genetic analysis"""
    
    # Color Scheme - Professional Medical Theme
    PRIMARY_COLOR = colors.HexColor('#1e3a5f')  # Dark blue
    SECONDARY_COLOR = colors.HexColor('#4a90d9')  # Light blue
    ACCENT_COLOR = colors.HexColor('#0369a1')  # Blue accent
    SUCCESS_COLOR = colors.HexColor('#059669')  # Green
    WARNING_COLOR = colors.HexColor('#d97706')  # Orange
    DANGER_COLOR = colors.HexColor('#dc2626')  # Red
    LIGHT_BG = colors.HexColor('#f8fafc')  # Light gray background
    BORDER_COLOR = colors.HexColor('#e2e8f0')  # Border gray
    
    def __init__(self, analysis_data: dict, user_info: dict = None):
        """
        Initialize the PDF generator
        
        Args:
            analysis_data: Dictionary containing analysis results from AnalysisHistory
            user_info: Optional dict with user name and email
        """
        self.analysis = analysis_data
        self.full_results = analysis_data.get('full_results', {})
        self.user_info = user_info or {}
        self.report_id = f"GNV-{datetime.now().strftime('%Y%m%d')}-{analysis_data.get('id', '0'):04d}"
        self.report_date = datetime.now()
        self.styles = self._create_styles()
        
    def _create_styles(self):
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtitle
        styles.add(ParagraphStyle(
            name='ReportSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#666666'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        # Section Header
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold',
            borderPadding=(0, 0, 5, 0),
        ))
        
        # Subsection Header
        styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=self.ACCENT_COLOR,
            spaceBefore=10,
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))
        
        # Body text (custom - renamed to avoid conflict with built-in BodyText)
        styles.add(ParagraphStyle(
            name='ReportBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            spaceBefore=3,
            spaceAfter=3,
            leading=14,
            fontName='Helvetica'
        ))
        
        # Small text
        styles.add(ParagraphStyle(
            name='SmallText',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6b7280'),
            fontName='Helvetica'
        ))
        
        # Label style
        styles.add(ParagraphStyle(
            name='Label',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#64748b'),
            fontName='Helvetica'
        ))
        
        # Value style
        styles.add(ParagraphStyle(
            name='Value',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.PRIMARY_COLOR,
            fontName='Helvetica-Bold'
        ))
        
        # Large value
        styles.add(ParagraphStyle(
            name='LargeValue',
            parent=styles['Normal'],
            fontSize=16,
            textColor=self.ACCENT_COLOR,
            fontName='Helvetica-Bold'
        ))
        
        # Disclaimer
        styles.add(ParagraphStyle(
            name='Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#64748b'),
            leading=11,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        ))
        
        # Footer
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#94a3b8'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
        return styles
    
    def _create_header(self):
        """Create report header with logo and report info"""
        elements = []
        
        # Header table with logo and report info
        header_data = [
            [
                Paragraph('<font color="#1e3a5f" size="22"><b>GENOVA</b></font>'
                         '<font color="#4a90d9" size="22"><b>AI</b></font>', self.styles['Normal']),
                Paragraph(f'<font size="9" color="#888888">Report ID</font><br/>'
                         f'<font size="11" color="#1e3a5f"><b>{self.report_id}</b></font>', 
                         ParagraphStyle('Right', parent=self.styles['Normal'], alignment=TA_RIGHT))
            ],
            [
                Paragraph('<font size="9" color="#666666">GENETIC ANALYSIS LABORATORY</font>', self.styles['Normal']),
                Paragraph(f'<font size="9" color="#888888">Generated</font><br/>'
                         f'<font size="10" color="#1e3a5f">{self.report_date.strftime("%B %d, %Y")}</font>',
                         ParagraphStyle('Right', parent=self.styles['Normal'], alignment=TA_RIGHT))
            ]
        ]
        
        header_table = Table(header_data, colWidths=[300, 180])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(header_table)
        
        # Header line
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=2, color=self.PRIMARY_COLOR, spaceAfter=15))
        
        # Report Title
        elements.append(Paragraph('Genetic Analysis Report', self.styles['ReportTitle']))
        elements.append(Paragraph('Comprehensive DNA Analysis Results', self.styles['ReportSubtitle']))
        
        return elements
    
    def _create_patient_info_section(self):
        """Create patient information section with optional generated portrait"""
        elements = []
        
        # Section header
        elements.append(Paragraph('Patient Information', self.styles['SectionHeader']))
        
        # Get patient data
        patient_name = self.user_info.get('name') or self.user_info.get('username') or 'Not Specified'
        patient_email = self.user_info.get('email') or ''
        sample_id = self.analysis.get('sample_id', 'N/A')
        created_at = self.analysis.get('created_at', '')
        if isinstance(created_at, str) and created_at:
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                analysis_date = created_at.strftime('%B %d, %Y at %H:%M')
            except:
                analysis_date = created_at
        else:
            analysis_date = self.report_date.strftime('%B %d, %Y at %H:%M')
        
        # Patient info table (smaller width to accommodate image)
        info_data = [
            ['Patient Name:', patient_name],
            ['Sample ID:', sample_id],
            ['Analysis Date:', analysis_date],
            ['Report Date:', self.report_date.strftime('%B %d, %Y %H:%M')],
            ['Status:', self.analysis.get('status', 'Completed').title()],
        ]
        
        if patient_email:
            info_data.append(['Email:', patient_email])
        
        info_table = Table(info_data, colWidths=[90, 200])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
            ('TEXTCOLOR', (1, 0), (1, -1), self.PRIMARY_COLOR),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, self.BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Check for generated portrait image
        image_path = self.full_results.get('generated_image_path', '')
        portrait_element = None
        
        if image_path:
            # Try to find the image file
            image_filename = os.path.basename(image_path)
            # Check in uploads folder
            possible_paths = [
                os.path.join(os.getcwd(), 'uploads', image_filename),
                os.path.join('/app/uploads', image_filename),
                image_path
            ]
            
            for img_path in possible_paths:
                if os.path.exists(img_path):
                    try:
                        # Create portrait image with styling
                        portrait_img = Image(img_path, width=120, height=150)
                        
                        # Wrap image in a table for border/styling
                        portrait_data = [
                            [portrait_img],
                            [Paragraph('<font size="8" color="#64748b">AI Portrait</font>', 
                                       ParagraphStyle('Center', parent=self.styles['Normal'], alignment=TA_CENTER))]
                        ]
                        portrait_table = Table(portrait_data, colWidths=[130])
                        portrait_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#bae6fd')),
                            ('PADDING', (0, 0), (-1, -1), 5),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        portrait_element = portrait_table
                        break
                    except Exception as e:
                        print(f"Failed to load portrait image: {e}")
        
        # Create main layout: info table on left, portrait on right (if available)
        if portrait_element:
            main_layout = Table(
                [[info_table, portrait_element]],
                colWidths=[310, 150]
            )
            main_layout.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ]))
            elements.append(main_layout)
        else:
            elements.append(info_table)
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_genetic_profile_section(self):
        """Create genetic profile summary section"""
        elements = []
        
        elements.append(Paragraph('Genetic Profile Summary', self.styles['SectionHeader']))
        
        # Get prediction data
        gender = self.analysis.get('gender_prediction', 'Not Analyzed')
        gender_confidence = self.analysis.get('gender_confidence')
        ancestry = self.analysis.get('ancestry_prediction', 'Not Analyzed')
        ancestry_code = self.analysis.get('ancestry_code', '')
        ancestry_confidence = self.analysis.get('ancestry_confidence')
        
        # Get population info
        pop_info = POPULATION_INFO.get(ancestry_code, {})
        pop_description = pop_info.get('description', '')
        
        # Create two-column layout for genetic profile
        col_width = 230
        
        # Gender box
        gender_conf_text = f"{gender_confidence*100:.1f}%" if gender_confidence else "N/A"
        gender_data = [
            [Paragraph('<font size="9" color="#64748b">BIOLOGICAL SEX</font>', self.styles['Normal'])],
            [Paragraph(f'<font size="16" color="#0369a1"><b>{gender}</b></font>', self.styles['Normal'])],
            [Paragraph(f'<font size="9" color="#64748b">Confidence: {gender_conf_text}</font>', self.styles['Normal'])],
        ]
        
        gender_table = Table(gender_data, colWidths=[col_width])
        gender_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Ancestry box
        ancestry_conf_text = f"{ancestry_confidence*100:.1f}%" if ancestry_confidence else "N/A"
        ancestry_display = f"{ancestry} ({ancestry_code})" if ancestry_code else ancestry
        ancestry_data = [
            [Paragraph('<font size="9" color="#64748b">GENETIC ANCESTRY</font>', self.styles['Normal'])],
            [Paragraph(f'<font size="16" color="#0369a1"><b>{ancestry_display}</b></font>', self.styles['Normal'])],
            [Paragraph(f'<font size="9" color="#64748b">{pop_description[:50]}...</font>' if len(pop_description) > 50 
                      else f'<font size="9" color="#64748b">{pop_description}</font>', self.styles['Normal'])],
        ]
        
        ancestry_table = Table(ancestry_data, colWidths=[col_width])
        ancestry_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        # Combine in a row
        profile_table = Table([[gender_table, ancestry_table]], colWidths=[col_width + 10, col_width + 10])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
            ('PADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(profile_table)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_physical_characteristics_section(self):
        """Create physical characteristics section with proper formatting"""
        elements = []
        
        physical_chars = self.analysis.get('physical_characteristics', '')
        if not physical_chars:
            return elements
        
        elements.append(Paragraph('Predicted Physical Characteristics', self.styles['SectionHeader']))
        
        # Try to parse as JSON first
        try:
            if isinstance(physical_chars, str):
                chars_data = json.loads(physical_chars)
            else:
                chars_data = physical_chars
            
            if isinstance(chars_data, dict):
                # Process and format characteristics properly
                char_items = []
                
                # Define display order (removed emojis - they don't render in PDF)
                display_order = ['hair', 'eyes', 'skin', 'face', 'body', 'traits']
                
                for key in display_order:
                    if key in chars_data:
                        value = chars_data[key]
                        # Format the value properly
                        if isinstance(value, dict):
                            # Extract nested values nicely
                            formatted_parts = []
                            for sub_key, sub_value in value.items():
                                if sub_key not in ['success', 'error']:
                                    formatted_parts.append(f"{sub_key.title()}: {sub_value}")
                            formatted_value = '\n'.join(formatted_parts)
                        else:
                            formatted_value = str(value)
                        
                        label = key.replace('_', ' ').title()
                        char_items.append((label, formatted_value))
                
                # Add any remaining keys not in display_order
                for key, value in chars_data.items():
                    if key not in display_order and key not in ['success', 'error', 'raw_response']:
                        if isinstance(value, dict):
                            formatted_parts = []
                            for sub_key, sub_value in value.items():
                                formatted_parts.append(f"{sub_key.title()}: {sub_value}")
                            formatted_value = '\n'.join(formatted_parts)
                        else:
                            formatted_value = str(value)
                        label = key.replace('_', ' ').title()
                        char_items.append((label, formatted_value))
                
                if char_items:
                    # Create rows of 3 items each
                    rows = []
                    for i in range(0, len(char_items), 3):
                        row = []
                        for j in range(3):
                            if i + j < len(char_items):
                                label, value = char_items[i + j]
                                # Create nicely formatted cell
                                cell_content = [
                                    [Paragraph(f'<font size="9" color="#1e3a5f"><b>{label.upper()}</b></font>', self.styles['Normal'])],
                                    [Spacer(1, 4)],
                                    [Paragraph(f'<font size="9" color="#374151">{value}</font>', self.styles['Normal'])]
                                ]
                                cell = Table(cell_content, colWidths=[145])
                                cell.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                                    ('PADDING', (0, 0), (-1, -1), 8),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                ]))
                                row.append(cell)
                            else:
                                row.append('')
                        rows.append(row)
                    
                    chars_table = Table(rows, colWidths=[155, 155, 155])
                    chars_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
                        ('PADDING', (0, 0), (-1, -1), 6),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    elements.append(chars_table)
        except (json.JSONDecodeError, TypeError) as e:
            # Display as text if not JSON
            if physical_chars and str(physical_chars).strip():
                import re
                clean_text = re.sub(r'<[^>]+>', '', str(physical_chars))
                elements.append(Paragraph(clean_text[:500], self.styles['ReportBody']))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _create_disease_risk_section(self):
        """Create disease risk assessment section with formatted disease cards"""
        elements = []
        
        disease_risk = self.analysis.get('disease_risk_report', '')
        if not disease_risk:
            return elements
        
        elements.append(Paragraph('Genetic Risk Assessment', self.styles['SectionHeader']))
        
        # Try to parse as JSON (diseases array)
        try:
            if isinstance(disease_risk, str):
                diseases = json.loads(disease_risk)
            else:
                diseases = disease_risk
            
            if isinstance(diseases, list) and len(diseases) > 0:
                # Create disease cards
                for disease in diseases:
                    if isinstance(disease, dict):
                        name = disease.get('name', 'Unknown Disease')
                        risk_level = disease.get('risk', 'unknown').lower()
                        genes = disease.get('genes', 'N/A')
                        prevalence = disease.get('prevalence', 'N/A')
                        description = disease.get('description', '')
                        
                        # Risk level colors
                        risk_colors = {
                            'high': ('#dc2626', '#fef2f2', '#fecaca'),
                            'moderate': ('#d97706', '#fffbeb', '#fde68a'),
                            'low': ('#059669', '#f0fdf4', '#bbf7d0'),
                        }
                        text_color, bg_color, border_color = risk_colors.get(risk_level, ('#6b7280', '#f9fafb', '#e5e7eb'))
                        
                        # Create disease card content
                        card_data = [
                            [
                                Paragraph(f'<font size="11" color="{text_color}"><b>{name}</b></font>', self.styles['Normal']),
                                Paragraph(f'<font size="9" color="{text_color}"><b>{risk_level.upper()} RISK</b></font>', self.styles['Normal'])
                            ],
                            [
                                Paragraph(f'<font size="8" color="#64748b">Genes: {genes}</font>', self.styles['Normal']),
                                Paragraph(f'<font size="8" color="#64748b">Prevalence: {prevalence}</font>', self.styles['Normal'])
                            ],
                            [
                                Paragraph(f'<font size="9" color="#374151">{description}</font>', self.styles['Normal']),
                                ''
                            ]
                        ]
                        
                        card = Table(card_data, colWidths=[320, 140])
                        card.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_color)),
                            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(border_color)),
                            ('LEFTPADDING', (0, 0), (-1, -1), 10),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('SPAN', (0, 2), (1, 2)),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('ALIGN', (1, 0), (1, 1), 'RIGHT'),
                        ]))
                        
                        elements.append(card)
                        elements.append(Spacer(1, 6))
            else:
                # Fallback: display as text
                raise ValueError("Not a diseases array")
                
        except (json.JSONDecodeError, TypeError, ValueError):
            # Display as plain text if not JSON array
            import re
            clean_text = re.sub(r'<[^>]+>', '', str(disease_risk))
            if clean_text.strip():
                risk_content = [
                    [Paragraph(clean_text[:1500] if len(clean_text) > 1500 else clean_text, 
                              ParagraphStyle('RiskText', parent=self.styles['ReportBody'], 
                                            textColor=colors.HexColor('#374151'), leading=14))]
                ]
                
                risk_table = Table(risk_content, colWidths=[460])
                risk_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
                    ('PADDING', (0, 0), (-1, -1), 12),
                ]))
                elements.append(risk_table)
        
        # Clinical note
        elements.append(Spacer(1, 10))
        note_data = [[Paragraph(
            '<font color="#c2410c"><b>Clinical Note:</b> These risk assessments are based on genetic markers '
            'and should be interpreted by a qualified healthcare professional. They do not constitute a medical diagnosis.</font>',
            ParagraphStyle('Note', parent=self.styles['SmallText'], textColor=colors.HexColor('#c2410c'))
        )]]
        note_table = Table(note_data, colWidths=[480])
        note_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fff7ed')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0, colors.white),
            ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor('#f97316')),
        ]))
        elements.append(note_table)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_health_guidance_section(self):
        """Create AI Health Guidance section with personalized recommendations - styled like disease risk cards"""
        elements = []
        
        # Get health guidance data from full_results
        guidance_data = self.full_results.get('health_guidance', {})
        if not guidance_data:
            # Try to generate guidance if we have disease data
            disease_risk = self.analysis.get('disease_risk_report', '')
            if disease_risk:
                try:
                    import json
                    from services import get_ai_health_guidance
                    
                    if isinstance(disease_risk, str):
                        diseases = json.loads(disease_risk)
                    else:
                        diseases = disease_risk
                    
                    if isinstance(diseases, list) and len(diseases) > 0:
                        gender = self.analysis.get('gender_prediction', 'Unknown')
                        population = self.analysis.get('ancestry_prediction', 'Unknown')
                        
                        result = get_ai_health_guidance(diseases, gender, population)
                        if result.get('success'):
                            guidance_data = result.get('guidance', {})
                except Exception as e:
                    print(f"Could not generate health guidance for PDF: {e}")
        
        if not guidance_data:
            return elements
        
        elements.append(Paragraph('AI Health Guidance', self.styles['SectionHeader']))
        elements.append(Spacer(1, 8))
        
        # Category definitions with icons and colors (matching disease risk style)
        categories = [
            ('nutrition', '🍎 Nutrition & Diet', '#10b981', '#f0fdf4', '#bbf7d0', guidance_data.get('nutrition', [])),
            ('lifestyle', '🏃 Lifestyle & Exercise', '#3b82f6', '#eff6ff', '#bfdbfe', guidance_data.get('lifestyle', [])),
            ('screenings', '🩺 Preventive Screenings', '#8b5cf6', '#faf5ff', '#e9d5ff', guidance_data.get('screenings', [])),
            ('wellness', '🧘 Wellness Tips', '#f59e0b', '#fffbeb', '#fde68a', guidance_data.get('wellness', []))
        ]
        
        # Create cards like disease risk section
        for cat_id, cat_name, text_color, bg_color, border_color, tips in categories:
            if not tips:
                continue
            
            # Build tips as bullet points
            tips_text = '  •  '.join(tips[:4])
            
            # Create card content matching disease risk style
            card_data = [
                [
                    Paragraph(f'<font size="11" color="{text_color}"><b>{cat_name}</b></font>', self.styles['Normal']),
                    Paragraph(f'<font size="9" color="{text_color}"><b>RECOMMENDATION</b></font>', self.styles['Normal'])
                ],
                [
                    Paragraph(f'<font size="9" color="#374151">• {tips[0] if len(tips) > 0 else ""}</font>', self.styles['Normal']),
                    ''
                ],
                [
                    Paragraph(f'<font size="9" color="#374151">• {tips[1] if len(tips) > 1 else ""}</font>', self.styles['Normal']),
                    ''
                ],
                [
                    Paragraph(f'<font size="9" color="#374151">• {tips[2] if len(tips) > 2 else ""}</font>', self.styles['Normal']),
                    ''
                ],
            ]
            
            # Add 4th tip if exists
            if len(tips) > 3:
                card_data.append([
                    Paragraph(f'<font size="9" color="#374151">• {tips[3]}</font>', self.styles['Normal']),
                    ''
                ])
            
            card = Table(card_data, colWidths=[360, 100])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(bg_color)),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(border_color)),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('SPAN', (0, 1), (1, 1)),
                ('SPAN', (0, 2), (1, 2)),
                ('SPAN', (0, 3), (1, 3)),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ]))
            
            elements.append(card)
            elements.append(Spacer(1, 6))
        
        # Clinical note (same style as disease risk section)
        elements.append(Spacer(1, 10))
        note_data = [[Paragraph(
            '<font color="#0369a1"><b>Wellness Note:</b> These recommendations are personalized based on your genetic profile '
            'and should complement, not replace, professional medical advice. Consult your healthcare provider before making significant changes.</font>',
            ParagraphStyle('Note', parent=self.styles['SmallText'], textColor=colors.HexColor('#0369a1'))
        )]]
        note_table = Table(note_data, colWidths=[480])
        note_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0, colors.white),
            ('LINEBEFORE', (0, 0), (0, -1), 3, colors.HexColor('#0ea5e9')),
        ]))
        elements.append(note_table)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_analysis_metadata_section(self):
        """Create analysis metadata section"""
        elements = []
        
        elements.append(Paragraph('Analysis Details', self.styles['SectionHeader']))
        
        # Gather metadata
        snp_count = self.analysis.get('snp_count', 'N/A')
        processing_time = self.analysis.get('processing_time')
        file_name = self.analysis.get('file_name', 'N/A')
        analysis_type = self.analysis.get('analysis_type', 'Combined Analysis')
        
        processing_time_str = f"{processing_time:.2f} seconds" if processing_time else 'N/A'
        
        meta_data = [
            ['Analysis Type:', analysis_type.replace('_', ' ').title(), 'SNPs Analyzed:', str(snp_count)],
            ['Input File:', file_name[:40] + '...' if len(str(file_name)) > 40 else str(file_name), 
             'Processing Time:', processing_time_str],
        ]
        
        meta_table = Table(meta_data, colWidths=[100, 140, 100, 140])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.LIGHT_BG),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#64748b')),
            ('TEXTCOLOR', (1, 0), (1, -1), self.PRIMARY_COLOR),
            ('TEXTCOLOR', (3, 0), (3, -1), self.PRIMARY_COLOR),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 1, self.BORDER_COLOR),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, self.BORDER_COLOR),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(meta_table)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_disclaimer_section(self):
        """Create disclaimer section"""
        elements = []
        
        elements.append(Paragraph('Important Information', self.styles['SectionHeader']))
        
        disclaimer_text = (
            "This genetic analysis report is generated by GenovaAI using advanced machine learning algorithms "
            "and SNP (Single Nucleotide Polymorphism) analysis. The results presented herein are for "
            "informational and research purposes only and should not be used as a substitute for professional "
            "medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider "
            "for medical decisions. The accuracy of predictions may vary based on the quality and completeness "
            "of the genetic data provided. This report does not diagnose any medical condition and should not "
            "be used as the sole basis for any medical treatment decisions."
        )
        
        disclaimer_data = [[Paragraph(disclaimer_text, self.styles['Disclaimer'])]]
        disclaimer_table = Table(disclaimer_data, colWidths=[480])
        disclaimer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f5f9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('PADDING', (0, 0), (-1, -1), 15),
        ]))
        
        elements.append(disclaimer_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_footer(self):
        """Create report footer"""
        elements = []
        
        elements.append(HRFlowable(width="100%", thickness=1, color=self.BORDER_COLOR, spaceBefore=10))
        
        footer_data = [
            [
                Paragraph('<font size="10" color="#1e3a5f"><b>GenovaAI Genetic Analysis Platform</b></font><br/>'
                         '<font size="8" color="#94a3b8">Advanced DNA Analysis &amp; Risk Assessment</font>', 
                         self.styles['Normal']),
                Paragraph(f'<font size="8" color="#94a3b8">Report generated automatically<br/>'
                         f'{self.report_date.strftime("%B %d, %Y at %H:%M")}</font>',
                         ParagraphStyle('Right', parent=self.styles['Normal'], alignment=TA_RIGHT))
            ]
        ]
        
        footer_table = Table(footer_data, colWidths=[280, 200])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(footer_table)
        
        return elements
    
    def generate(self) -> BytesIO:
        """
        Generate the PDF report
        
        Returns:
            BytesIO buffer containing the PDF
        """
        buffer = BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
            title=f"GenovaAI Genetic Analysis Report - {self.analysis.get('sample_id', 'Report')}",
            author="GenovaAI Genetic Analysis Platform"
        )
        
        # Build content
        elements = []
        
        # Add sections
        elements.extend(self._create_header())
        elements.extend(self._create_patient_info_section())
        elements.extend(self._create_genetic_profile_section())
        elements.extend(self._create_physical_characteristics_section())
        
        # Disease Risk on Page 2 for cleaner layout
        elements.append(PageBreak())
        elements.extend(self._create_disease_risk_section())
        
        # Health Guidance on Page 3
        elements.append(PageBreak())
        elements.extend(self._create_health_guidance_section())
        
        # elements.extend(self._create_analysis_metadata_section())  # Removed - not needed in report
        elements.extend(self._create_disclaimer_section())
        elements.extend(self._create_footer())
        
        # Build PDF
        doc.build(elements)
        
        buffer.seek(0)
        return buffer
    
    def save_to_file(self, filepath: str) -> str:
        """
        Generate and save PDF to file
        
        Args:
            filepath: Path to save the PDF
            
        Returns:
            The filepath where the PDF was saved
        """
        buffer = self.generate()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(buffer.read())
        
        return filepath


def generate_medical_report(analysis_data: dict, user_info: dict = None, save_path: str = None) -> tuple:
    """
    Generate a professional medical PDF report for genetic analysis
    
    Args:
        analysis_data: Dictionary containing analysis results (from AnalysisHistory.to_dict())
        user_info: Optional dict with 'name' and 'email' keys for patient info
        save_path: Optional path to save the PDF file. If None, returns buffer only.
        
    Returns:
        Tuple of (BytesIO buffer, filepath or None)
    """
    generator = MedicalReportPDF(analysis_data, user_info)
    
    if save_path:
        filepath = generator.save_to_file(save_path)
        buffer = generator.generate()  # Generate fresh buffer for return
        return buffer, filepath
    else:
        buffer = generator.generate()
        return buffer, None


def get_report_filename(sample_id: str, analysis_id: int = None) -> str:
    """
    Generate a standardized report filename
    
    Args:
        sample_id: The sample identifier
        analysis_id: Optional analysis ID
        
    Returns:
        Formatted filename string
    """
    date_str = datetime.now().strftime('%Y%m%d')
    if analysis_id:
        return f"{sample_id}_GenovaAI_Report_{analysis_id}_{date_str}.pdf"
    return f"{sample_id}_GenovaAI_Report_{date_str}.pdf"
