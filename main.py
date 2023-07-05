import streamlit as st
import pandas as pd
from difflib import SequenceMatcher
import io

st.set_page_config(page_title='Data Matcher', page_icon=':computer:', layout='centered')
st.title("Assessment Data Matcher")

buffer = io.BytesIO()


def find_best_match(name, name_list):
    best_score = 0
    best_match = None
    for n in name_list:
        score = SequenceMatcher(None, name, n).ratio()
        if score > best_score:
            best_score = score
            best_match = n
    if best_score >= 0.9:
        return best_match
    else:
        return None


def per_assessment(pat_file, classlist, header):
    original_df = pd.read_excel(pat_file, header=None, nrows=header + 1)
    assessment_df = pd.read_excel(pat_file, header=header)
    students_df = pd.read_excel(classlist)
    listo = []
    changes = []
    for i, row in assessment_df.iterrows():
        student_name = row['Given name'].title() + ' ' + row['Family name'].title()
        matching_names = students_df['First Name'] + ' ' + students_df['Last Name']
        matching_name = find_best_match(student_name, matching_names)

        if matching_name:
            student_info = students_df.loc[matching_names == matching_name].iloc[0]
            if assessment_df.loc[i, 'Given name'] != student_info['First Name']:
                assessment_df.loc[i, 'Given name'] = student_info['First Name']
                changes.append(f'ROW: {i+header + 2} CHANGED FIRST NAME')
            if assessment_df.loc[i, 'Family name'] != student_info['Last Name']:
                assessment_df.loc[i, 'Family name'] = student_info['Last Name']
                changes.append(f'ROW: {i + header + 2} CHANGED LAST NAME')
            if assessment_df.loc[i, 'DOB'] != student_info['Birth Date']:
                changes.append(f'ROW: {i + header + 2} CHANGED DOB')
                assessment_df.loc[i, 'DOB'] = student_info['Birth Date']
            if assessment_df.loc[i, 'Gender'] != student_info['Gender']:
                changes.append(f'ROW: {i + header + 2} CHANGED GENDER')
                assessment_df.loc[i, 'Gender'] = student_info['Gender']

        else:
            listo.append(
                f'ROW: {i + header + 2}, FIRST NAME: {student_name.split()[0]}, LAST NAME: {student_name.split()[1]}, DOB: {row["DOB"]}, GENDER: {row["Gender"]}')
    if len(listo) == 0:
        print(original_df)
        new_header = assessment_df.iloc[0]
        df = assessment_df[1:]  # take the data less the header row
        df.columns = new_header
        return df, changes
    return listo


with st.form("Main Form", clear_on_submit=False):
    pat_file = st.file_uploader('Upload PAT Files Here', type=None, accept_multiple_files=True, key=None,
                                help=None,
                                on_change=None, args=None,
                                kwargs=None, disabled=False, label_visibility="visible")

    classlist = st.file_uploader('Upload Classlist here', type=None, accept_multiple_files=False, key=None,
                                 help=None,
                                 on_change=None, args=None,
                                 kwargs=None, disabled=False, label_visibility="visible")

    submitted = st.form_submit_button("Submit")

if submitted and classlist:
    for files in sorted(pat_file, key=lambda a: a.name):
        try:
            result = per_assessment(files, classlist, 11)
        except:
            result = per_assessment(files, classlist, 12)

        col1, col2, = st.columns(2)
        if type(result) == list:
            with col1:
                st.error(f'Issues with {files.name} detected')
            with col2:
                st.write(result)
        else:
            with col1:
                if not result[1]:
                    st.success(f'File {files.name} looks good to go')
                else:
                    st.warning(result[1])
            with col2:
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    result[0].to_excel(writer, sheet_name='Sheet1', index=False)
                    writer.close()
                    st.download_button(
                        label=files.name,
                        data=buffer,
                        file_name=files.name,
                        mime="application/vnd.ms-excel")
        st.write('---')
