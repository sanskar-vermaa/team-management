import json
import os

from flask import Flask, request, render_template, send_file, flash, redirect, url_for
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

ALLOWED_EXTENSIONS = {'.xlsx', '.xls'}
REQUIRED_COLUMNS = ['Dev', 'BA', 'DA']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or request.files['file'].filename == '':
        flash('Please choose an Excel file to upload.')
        return redirect(url_for('index'))

    file = request.files['file']
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        flash('Unsupported file type. Please upload a .xlsx or .xls file.')
        return redirect(url_for('index'))

    try:
        dev_size = max(1, int(request.form.get('dev_size', 3)))
    except ValueError:
        dev_size = 3

    try:
        df = pd.read_excel(file)
    except Exception:
        flash('Could not read that file. Make sure it is a valid Excel file.')
        return redirect(url_for('index'))

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        flash(f"The uploaded file is missing required column(s): {', '.join(missing)}")
        return redirect(url_for('index'))

    teams, leftovers = generate_teams(df, dev_size)
    if not teams:
        flash('Not enough people in one or more roles to form a single team.')
        return redirect(url_for('index'))

    return render_template(
        'results.html',
        teams=teams,
        leftovers=leftovers,
        teams_json=json.dumps(teams),
    )


@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    teams = json.loads(request.form.get('teams_json', '[]'))
    if not teams:
        flash('Nothing to download.')
        return redirect(url_for('index'))
    pdf = create_pdf(teams)
    return send_file(pdf, as_attachment=True, download_name='teams.pdf', mimetype='application/pdf')


def generate_teams(df, dev_size=3):
    devs = df['Dev'].dropna().tolist()
    bas = df['BA'].dropna().tolist()
    das = df['DA'].dropna().tolist()

    teams = []
    while len(devs) >= dev_size and len(bas) >= 1 and len(das) >= 1:
        team = {
            'Dev': devs[:dev_size],
            'BA': bas[:1],
            'DA': das[:1],
        }
        teams.append(team)
        devs = devs[dev_size:]
        bas = bas[1:]
        das = das[1:]

    leftovers = {'Dev': devs, 'BA': bas, 'DA': das}
    return teams, leftovers


def create_pdf(teams):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph('Team Compositions', styles['Title']), Spacer(1, 16)]

    for i, team in enumerate(teams, start=1):
        elements.append(Paragraph(f'Team {i}', styles['Heading2']))
        rows = [['Role', 'Member']]
        for role, members in team.items():
            for member in members:
                rows.append([role, member])
        table = Table(rows, colWidths=[100, 300])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f4f5')]),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 20))

    doc.build(elements)
    buffer.seek(0)
    return buffer


if __name__ == '__main__':
    app.run(debug=True)
