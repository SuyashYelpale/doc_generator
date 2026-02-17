from flask import Flask, render_template, request, redirect, url_for, session, send_file, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from xhtml2pdf import pisa
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import io
import zipfile

from config import COMPANIES

app = Flask(__name__)
app.secret_key = "super-secret-key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///documents.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, "generated_docs")
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Auto Increment
    full_name = db.Column(db.String(100))
    aadhar_no = db.Column(db.String(20))
    designation = db.Column(db.String(100))
    ctc = db.Column(db.Float)
    increment_per_month = db.Column(db.Float, default=0)
    resignation_date = db.Column(db.Date, nullable=True)

def html_to_pdf(html_content, output_path):
    """
    Safe HTML to PDF converter
    Handles None values and table width issues
    """

    try:
        # Replace None values with empty string
        if html_content:
            html_content = html_content.replace("None", "")

        # Add safe CSS to avoid negative width error
        safe_style = """
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            td, th {
                padding: 5px;
                word-wrap: break-word;
            }
            body {
                font-family: Arial, sans-serif;
            }
        </style>
        """

        # Inject safe CSS inside HTML
        if "<head>" in html_content:
            html_content = html_content.replace("<head>", "<head>" + safe_style)
        else:
            html_content = safe_style + html_content

        # Create folder if not exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Generate PDF
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=pdf_file
            )

        return not pisa_status.err

    except Exception as e:
        print("PDF Generation Error:", e)
        return False

@app.template_filter('humanize')
def humanize_filter(value):
    try:
        num = float(value)
        return intword(num)
    except (ValueError, TypeError):
        return str(value)

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

def get_previous_workday(target_date, days_before):
    count = 0
    while count < days_before:
        target_date -= timedelta(days=1)
        if target_date.weekday() < 5:
            count += 1
    return target_date

def convert_dates(form_data):
    date_fields = ['joining_date', 'resignation_date']
    for field in date_fields:
        if field in form_data and form_data[field]:
            try:
                form_data[field] = datetime.strptime(form_data[field], '%Y-%m-%d')
            except (ValueError, TypeError):
                form_data[field] = None
    return form_data

def generate_pdf_file(form_data, company, doc_type):
    template = f"templates/documents/{doc_type}.html"
    html_content = render_template(template.replace('templates/', ''), data=form_data, company=company)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{doc_type}_{form_data['full_name']}_{timestamp}.pdf"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    success = html_to_pdf(html_content, filepath)
    if success:
        return filename
    else:
        raise Exception("Failed to generate PDF")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        full_name = request.form.get('full_name')
        aadhar_no = request.form.get('aadhar_no')

        existing_employee = Employee.query.filter_by(
            full_name=full_name,
            aadhar_no=aadhar_no
        ).first()

        if existing_employee:
            employee = existing_employee
        else:
            employee = Employee(
                full_name=full_name,
                aadhar_no=aadhar_no,
                designation=request.form.get('designation'),
                ctc=float(request.form.get('ctc') or 0)
            )
            db.session.add(employee)
            db.session.commit()

        employee_id = f"EMP{employee.id:04d}"

        # ✅ IMPORTANT FIX — increment_per_month added
        form_data = {
            'employee_id': employee_id,
            'company': request.form.get('company'),
            'document_type': request.form.get('document_type'),
            'full_name': full_name,
            'address': request.form.get('address'),
            'aadhar_no': aadhar_no,
            'joining_date': request.form.get('joining_date'),
            'resignation_date': request.form.get('resignation_date'),
            'designation': request.form.get('designation'),
            'ctc': request.form.get('ctc') or 0,
            'increment_per_month': request.form.get('increment_per_month') or 0,  # 🔥 ADDED
            'bank_details': {
                'account_holder': request.form.get('account_holder'),
                'account_number': request.form.get('account_number'),
                'bank_name': request.form.get('bank_name'),
                'branch': request.form.get('branch'),
                'ifsc_code': request.form.get('ifsc_code')
            },
            'pan_no': request.form.get('pan_no')
        }

        selected_months = request.form.getlist('months')
        selected_year = request.form.get('year')

        session['selected_months'] = selected_months
        session['selected_year'] = selected_year
        session['form_data'] = form_data

        return redirect(url_for('preview'))

    return render_template('index.html', companies=COMPANIES)

@app.route('/preview')
def preview():
    form_data = session.get('form_data', {})
    
    selected_months = session.get('selected_months', [])
    if not form_data:
        return redirect(url_for('index'))

    form_data = convert_dates(form_data)

    if form_data.get('joining_date'):
        date_before = get_previous_workday(form_data['joining_date'], 8)
        form_data['date_before'] = date_before

    company = next((c for c in COMPANIES if c['id'] == form_data['company']), None)
    if not company:
        return "Company not found", 404

    ctc = float(form_data.get('ctc') or 0)
    increment_per_month = float(form_data.get('increment_per_month') or 0)

    monthly_ctc = round(ctc / 12)
    monthly_ctc_after_increment = monthly_ctc + increment_per_month

    basic = round(monthly_ctc_after_increment * 0.5)
    hra = round(basic * 0.5)
    conveyance = round(monthly_ctc_after_increment * 0.05)
    medical = round(monthly_ctc_after_increment * 0.014)
    telephone = round(monthly_ctc_after_increment * 0.02)

    special_allowance = monthly_ctc_after_increment - (
        basic + hra + conveyance + medical + telephone
    )

    professional_tax = 200
    gross_salary = basic + hra + conveyance + medical + telephone + special_allowance
    net_salary = gross_salary - professional_tax

    form_data['salary_breakdown'] = {
        'basic': basic,
        'hra': hra,
        'conveyance': conveyance,
        'medical': medical,
        'telephone': telephone,
        'special_allowance': special_allowance,
        'professional_tax': professional_tax,
        'gross_salary': gross_salary,
        'net_salary': net_salary,
        'increment_per_month': increment_per_month
    }

    form_data['monthly_ctc_after_increment'] = monthly_ctc_after_increment

    joining_date = form_data.get("joining_date")

    if joining_date:
        if isinstance(joining_date, str):
            joining_date_obj = datetime.strptime(joining_date, "%Y-%m-%d")
        else:
            joining_date_obj = joining_date   # already datetime

        form_data['formatted_joining_date'] = joining_date_obj.strftime("%d %B %Y")
    else:
        form_data['formatted_joining_date'] = None

    resignation_date = form_data.get("resignation_date")
    if resignation_date:
        if isinstance(resignation_date, str):
            resignation_date_obj = datetime.strptime(resignation_date, "%Y-%m-%d")
        else:
            resignation_date_obj = resignation_date   # already datetime

        form_data['formatted_resignation_date'] = resignation_date_obj.strftime("%d %B %Y")
        relieving_date = resignation_date_obj + timedelta(days=30)
        form_data['relieving_date'] = relieving_date.strftime("%d %B %Y")
    else:
        form_data['formatted_resignation_date'] = None
        form_data['relieving_date'] = None

    # Build a month label for preview when applicable (use first selected month)
    month_label = []
    if form_data.get('document_type') in ['salary_slip', 'offer_and_salary'] and selected_months:
        current_year = session.get('selected_year', datetime.now().year)
        for m in selected_months:
            m = m.strip()
            m = m[:1].upper() + m[1:].lower()
            month_label.append(f"{m} {current_year}")

    if form_data.get('document_type') == 'offer_and_salary':
        return render_template(
            'documents/offer_letter.html',
            data=form_data,
            company=company,
            months=selected_months,
            month=month_label,
            lc_logo="lc_logo.png"
        )

    template = f"documents/{form_data['document_type']}.html"
    return render_template(
        template,
        data=form_data,
        company=company,
        months=selected_months,
        month=month_label,
        lc_logo="lc_logo.png"
    )

@app.route('/preview_document/<doc_type>')
def preview_document(doc_type):
    form_data = session.get('form_data', {})
    
    selected_months = session.get('selected_months', [])
    if not form_data:
        return redirect(url_for('index'))

    form_data = convert_dates(form_data)

    if form_data.get('joining_date'):
        date_before = get_previous_workday(form_data['joining_date'], 8)
        form_data['date_before'] = date_before

    company = next((c for c in COMPANIES if c['id'] == form_data['company']), None)
    if not company:
        return "Company not found", 404

    ctc = float(form_data.get('ctc') or 0)
    increment_per_month = float(form_data.get('increment_per_month') or 0)

    monthly_ctc = round(ctc / 12)
    monthly_ctc_after_increment = monthly_ctc + increment_per_month

    basic = round(monthly_ctc_after_increment * 0.5)
    hra = round(basic * 0.5)
    conveyance = round(monthly_ctc_after_increment * 0.05)
    medical = round(monthly_ctc_after_increment * 0.014)
    telephone = round(monthly_ctc_after_increment * 0.02)

    special_allowance = monthly_ctc_after_increment - (
        basic + hra + conveyance + medical + telephone
    )

    professional_tax = 200
    gross_salary = basic + hra + conveyance + medical + telephone + special_allowance
    net_salary = gross_salary - professional_tax

    form_data['salary_breakdown'] = {
        'basic': basic,
        'hra': hra,
        'conveyance': conveyance,
        'medical': medical,
        'telephone': telephone,
        'special_allowance': special_allowance,
        'professional_tax': professional_tax,
        'gross_salary': gross_salary,
        'net_salary': net_salary,
        'increment_per_month': increment_per_month
    }

    form_data['monthly_ctc_after_increment'] = monthly_ctc_after_increment

    joining_date = form_data.get("joining_date")

    if joining_date:
        if isinstance(joining_date, str):
            joining_date_obj = datetime.strptime(joining_date, "%Y-%m-%d")
        else:
            joining_date_obj = joining_date   # already datetime

        form_data['formatted_joining_date'] = joining_date_obj.strftime("%d %B %Y")
    else:
        form_data['formatted_joining_date'] = None

    resignation_date = form_data.get("resignation_date")
    if resignation_date:
        if isinstance(resignation_date, str):
            resignation_date_obj = datetime.strptime(resignation_date, "%Y-%m-%d")
        else:
            resignation_date_obj = resignation_date   # already datetime

        form_data['formatted_resignation_date'] = resignation_date_obj.strftime("%d %B %Y")
        relieving_date = resignation_date_obj + timedelta(days=30)
        form_data['relieving_date'] = relieving_date.strftime("%d %B %Y")
    else:
        form_data['formatted_resignation_date'] = None
        form_data['relieving_date'] = None


    # month label for preview route
    month_label = None
    if doc_type in ['salary_slip'] and selected_months:
        m = selected_months[0].strip()
        m = m[:1].upper() + m[1:].lower()
        current_year = datetime.now().year
        month_label = f"{m} {current_year}"

    if form_data.get('document_type') == 'offer_and_salary' and doc_type == 'offer_letter':
        return render_template(
            'documents/offer_letter.html',
            data=form_data,
            company=company,
            months=selected_months,
            month=month_label,
            lc_logo="lc_logo.png"
        )

    template = f"documents/{doc_type}.html"
    return render_template(
        template,
        data=form_data,
        company=company,
        months=selected_months,
        month=month_label,
        lc_logo="lc_logo.png"
    )

@app.route('/generate', methods=['POST'])
def generate():

    form_data = session.get('form_data')
    selected_months = session.get('selected_months', [])

    if not form_data:
        return redirect(url_for('index'))

    employee_id = secure_filename(form_data.get('employee_id', 'unknown'))
    base_folder = os.path.join(app.config['UPLOAD_FOLDER'], "employee_documents")
    employee_folder = os.path.join(base_folder, employee_id)
    os.makedirs(employee_folder, exist_ok=True)

    doc_type = form_data.get('document_type')

    # -------------------------
    # SALARY CALCULATION LOGIC
    # -------------------------

    ctc = float(form_data.get('ctc') or 0)
    increment_per_month = float(form_data.get('increment_per_month') or 0)

    monthly_ctc = round(ctc / 12)

    # Apply increment
    monthly_ctc_after_increment = monthly_ctc + increment_per_month

    basic = round(monthly_ctc_after_increment * 0.5)
    hra = round(basic * 0.5)
    conveyance = round(monthly_ctc_after_increment * 0.05)
    medical = round(monthly_ctc_after_increment * 0.014)
    telephone = round(monthly_ctc_after_increment * 0.02)

    special_allowance = monthly_ctc_after_increment - (
        basic + hra + conveyance + medical + telephone
    )

    professional_tax = 200

    gross_salary = basic + hra + conveyance + medical + telephone + special_allowance
    net_salary = gross_salary - professional_tax

    form_data['salary_breakdown'] = {
        'basic': basic,
        'hra': hra,
        'conveyance': conveyance,
        'medical': medical,
        'telephone': telephone,
        'special_allowance': special_allowance,
        'professional_tax': professional_tax,
        'gross_salary': gross_salary,
        'net_salary': net_salary,
        'increment_per_month': increment_per_month
    }

    form_data['net_salary'] = net_salary
    form_data['monthly_ctc_after_increment'] = monthly_ctc_after_increment

    # -------------------------
    # DATE LOGIC FOR RESIGNATION / RELIEVING
    # -------------------------

    resignation_date = form_data.get('resignation_date')

    if resignation_date:
        resignation_date_obj = datetime.strptime(resignation_date, "%Y-%m-%d")
        form_data['formatted_resignation_date'] = resignation_date_obj.strftime("%d %B %Y")

        # 30 days notice period auto calculation
        relieving_date = resignation_date_obj + timedelta(days=30)
        form_data['relieving_date'] = relieving_date.strftime("%d %B %Y")
    else:
        form_data['formatted_resignation_date'] = None
        form_data['relieving_date'] = None

    company = next((c for c in COMPANIES if c['id'] == form_data.get('company')), None)

    # -------------------------
    # DATE FORMAT FIX
    # -------------------------

    joining_date = form_data.get("joining_date")

    if joining_date:
        joining_date_obj = datetime.strptime(joining_date, "%Y-%m-%d")
        form_data['formatted_joining_date'] = joining_date_obj.strftime("%d %B %Y")
    else:
        form_data['formatted_joining_date'] = None

    # -------------------------
    # SALARY SLIP (MULTIPLE MONTHS ZIP)
    # -------------------------

    if doc_type == "salary_slip" and selected_months:

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:

            for month in selected_months:
                form_data_copy = form_data.copy()
                form_data_copy['month'] = month

                html = render_template(
                    "documents/salary_slip.html",
                    data=form_data_copy,
                    company=company
                )

                filename = f"Salary_Slip_{month}.pdf"
                filepath = os.path.join(employee_folder, filename)

                html_to_pdf(html, filepath)
                zip_file.write(filepath, filename)

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f"{employee_id}_Salary_Slips.zip",
            mimetype="application/zip"
        )

    # -------------------------
    # OTHER DOCUMENTS
    # -------------------------

    html = render_template(
        f"documents/{doc_type}.html",
        data=form_data,
        company=company,
    )

    filename = f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(employee_folder, filename)

    html_to_pdf(html, filepath)

    return send_from_directory(employee_folder, filename, as_attachment=True)

@app.route('/generated_docs/<filename>')
def serve_generated_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/admin/documents')
def admin_documents():

    if not session.get('is_admin'):
        return "Unauthorized", 403

    base_folder = os.path.join(app.config['UPLOAD_FOLDER'], "employee_documents")

    if not os.path.exists(base_folder):
        os.makedirs(base_folder)

    data = {}

    for emp in os.listdir(base_folder):
        emp_path = os.path.join(base_folder, emp)
        if os.path.isdir(emp_path):
            data[emp] = os.listdir(emp_path)

    return render_template("admin_documents.html", data=data)

if __name__ == '__main__':
    app.run(debug=True)
