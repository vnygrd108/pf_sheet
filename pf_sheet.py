from flask import Flask, render_template, request, send_file
import pandas as pd
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['PROCESSED_FOLDER'] = './processed'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

def process_pf_excel(filepath):
    df = pd.read_excel(filepath)

    pf = df[['Employee Name','UAN Number','PF Number','Basic','DA','Employee PF','Actual Monthly Gross','HRA']].copy()
    pf['UAN Number'] = pf['UAN Number'].astype('Int64').astype(str)
    pf = pf.dropna()
    pf2 = pf.reset_index(drop=True)

    pf2['PF Salary'] = pf2.apply(lambda row: 15000 if (row['Actual Monthly Gross'] - row['HRA']) > 15000 else (row['Actual Monthly Gross'] - row['HRA']), axis=1)
    pf2['PF 12%'] = pf2['PF Salary'] * 0.12
    pf2['Pen'] = pf2['PF Salary'] * 0.0833
    pf2['Bal'] = pf2['PF 12%'] - pf2['Pen']
    pf_final = pf2[['UAN Number', 'PF Number', 'Employee Name', 'Actual Monthly Gross', 'PF Salary', 'PF 12%', 'Bal', 'Pen']].copy()
    pf_final.insert(0, 'Sr. No.', range(1, len(pf_final) + 1))

    columns_to_round = ['Actual Monthly Gross', 'PF Salary', 'PF 12%', 'Bal', 'Pen']
    pf_final[columns_to_round] = pf_final[columns_to_round].astype(float).round(1)

    output_path = os.path.join(app.config['PROCESSED_FOLDER'], 'PF_Data_2025-26.xlsx')
    pf_final.to_excel(output_path, index=False)

    return pf_final, output_path


@app.route('/', methods=['GET', 'POST'])
def index():
    pf_final_html = None
    download_link = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith(('.xlsx', '.xls')):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            pf_final, output_path = process_pf_excel(filepath)
            pf_final_html = pf_final.to_html(classes='table table-striped', index=False)
            download_link = '/download'

    return render_template('index.html', table=pf_final_html, download_link=download_link)


@app.route('/download')
def download():
    path = os.path.join(app.config['PROCESSED_FOLDER'], 'PF_Data_2025-26.xlsx')
    return send_file(path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
