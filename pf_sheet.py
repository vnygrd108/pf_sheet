from flask import Flask, render_template, request, send_file
import pandas as pd
import os
import numpy as np

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    table = None
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            # Read and process the Excel file
            df = pd.read_excel(file_path)
            pf = df[['Employee Name','UAN Number','PF Number','Basic','DA','Employee PF','Actual Monthly Gross', 'HRA']].copy()
            pf['Employee PF'] = pf['Employee PF'].replace(['', 'null', 'NULL'], np.nan)
            # Drop rows where Employee PF is 0 or null
            pf = pf[~((pf['Employee PF'].isna()) | (pf['Employee PF'] == 0))]
            pf['UAN Number'] = pf['UAN Number'].astype('Int64').astype(str)
            pf2 = pf.reset_index(drop=True)
            pf2['Total'] = pf2['Basic'] + pf2['DA']
            
            pf2['PF 12%'] = np.where(
                pf2['Actual Monthly Gross'] - pf2['HRA'] > 15000,
                1800,
                0.12 * (pf2['Actual Monthly Gross'] - pf2['HRA'])
            )

            pf2['Pen'] = pf2['Total'] * 0.0833
            pf2['Bal'] = pf2['PF 12%'] - pf2['Pen']
            cols_to_convert = ['PF 12%', 'Pen', 'Bal']
            pf2[cols_to_convert] = pf2[cols_to_convert].astype(int)
            pf3 = pf2[['Employee Name','UAN Number','PF Number','Basic','DA','Total','PF 12%','Bal','Pen','Actual Monthly Gross']]
            pf3.insert(0, 'Sr. No.', range(1, len(pf3) + 1))
            insert_pos = len(pf3.columns) - 1
            pf3.insert(insert_pos, 'Project', '')

            # Save to Excel
            output_path = 'Prayag_PF_Sheet_2025-26.xlsx'
            pf3.to_excel(output_path, index=False)

            # Show table in HTML
            table = pf3.to_html(index=False, classes='table table-bordered table-striped')
    
    return render_template('pf_sheet.html', table=table)

@app.route('/download')
def download():
    return send_file('Prayag_PF_Sheet_2025-26.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
