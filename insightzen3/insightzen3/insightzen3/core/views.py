"""
Views for handling user authentication and the dashboard.

This module defines function‑based views for sign‑up, login, logout
and displaying a simple dashboard and placeholder pages. The
dashboard and placeholder views are protected so that only logged
in users can access them. On successful registration the user is
redirected to the login page.
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

import base64
import json
import io
import time
from datetime import datetime
from functools import reduce

import pandas as pd  # type: ignore
import requests
import matplotlib.pyplot as plt  # type: ignore

from .forms import SignUpForm, LoginForm


def signup_view(request: HttpRequest) -> HttpResponse:
    """Render and process the user registration form."""
    lang = request.session.get('lang', 'en')  # Default language is English
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # Success message based on language
            if lang == 'fa':
                messages.success(request, 'ثبت‌نام با موفقیت انجام شد. اکنون می‌توانید وارد شوید.')
            else:
                messages.success(request, 'Registration successful. You can now log in.')
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form, 'lang': lang})


def login_view(request: HttpRequest) -> HttpResponse:
    """Render and process the login form."""
    lang = request.session.get('lang', 'en')  # Default language is English
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Retrieve the authenticated user from the form's cleaned_data
            user = form.cleaned_data.get('user')
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form, 'lang': lang})


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log the user out and redirect to the login page."""
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Display an empty dashboard with only the side menu."""
    lang = request.session.get('lang', 'en')
    return render(request, 'dashboard.html', {'lang': lang})


@login_required
def page1_view(request: HttpRequest) -> HttpResponse:
    """Placeholder page 1. Content intentionally left blank."""
    lang = request.session.get('lang', 'en')
    return render(request, 'page1.html', {'lang': lang})


@login_required
def page2_view(request: HttpRequest) -> HttpResponse:
    """Placeholder page 2. Content intentionally left blank."""
    lang = request.session.get('lang', 'en')
    return render(request, 'page2.html', {'lang': lang})


@login_required
def page3_view(request: HttpRequest) -> HttpResponse:
    """Placeholder page 3. Content intentionally left blank."""
    lang = request.session.get('lang', 'en')
    return render(request, 'page3.html', {'lang': lang})


def set_language(request: HttpRequest) -> HttpResponse:
    """
    View to change the user's preferred language. The language code is passed
    as a query parameter (?lang=en or ?lang=fa). The chosen language is
    stored in the session and the user is redirected back to the referring
    page or to the dashboard if no referrer is available.
    """
    lang = request.GET.get('lang', 'en')
    if lang not in ['en', 'fa']:
        lang = 'en'
    request.session['lang'] = lang
    # Redirect to previous page or dashboard
    next_url = request.META.get('HTTP_REFERER') or reverse('dashboard')
    return redirect(next_url)


@login_required
def coding_view(request: HttpRequest) -> HttpResponse:
    """
    Display and process the coding page. This view allows users to enter
    an API key, project name, question domain and upload an Excel file with
    specific sheets (codeframe, question, data). It will then send the
    appropriate prompts to the external x.ai API for each unique question ID
    (QID) in the question sheet, parse the returned codes using the logic
    from IR9.py and compile several DataFrames: a merged "triple" sheet,
    a codeframe summary and a binary sheet. A bar chart of counts by QID
    and code is generated with matplotlib. The results are rendered in
    the template along with a download link for the resulting Excel file.
    """
    lang = request.session.get('lang', 'en')
    context: dict[str, object] = {'lang': lang}

    # Provide default empty fields in context
    context.update({
        'api_key': '',
        'project_name': '',
        'question_domain': '',
    })

    if request.method == 'POST':
        # Extract posted data
        api_key = request.POST.get('api_key', '').strip()
        project_name = request.POST.get('project_name', '').strip()
        question_domain = request.POST.get('question_domain', '').strip()
        uploaded_file = request.FILES.get('uploaded_file')

        context.update({
            'api_key': api_key,
            'project_name': project_name,
            'question_domain': question_domain,
        })

        errors: list[str] = []

        # Translate generic error messages
        def trans(msg_en: str, msg_fa: str) -> str:
            return msg_fa if lang == 'fa' else msg_en

        # Validate the API key
        if not api_key:
            errors.append(trans('Please enter your API key.', 'لطفاً کلید API خود را وارد کنید.'))

        # Validate other fields
        if not project_name:
            errors.append(trans('Please enter a project name.', 'لطفاً نام پروژه را وارد کنید.'))
        if not question_domain:
            errors.append(trans('Please enter a question domain.', 'لطفاً حوزهٔ سؤال را وارد کنید.'))
        if uploaded_file is None:
            errors.append(trans('Please upload an Excel file.', 'لطفاً فایل اکسل را بارگذاری کنید.'))

        # If there are validation errors, send them to the template
        if errors:
            context['errors'] = errors
            return render(request, 'coding.html', context)

        # Test the API connection with a simple request
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        test_payload = {
            "model": "grok-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 1
        }
        try:
            test_response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=test_payload)
            test_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            context['errors'] = [trans('API connection failed: ', 'اتصال به API ناموفق بود: ') + str(e)]
            return render(request, 'coding.html', context)

        # Process uploaded Excel file
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            required_sheets = ["codeframe", "question", "data"]
            missing = [s for s in required_sheets if s not in excel_data.sheet_names]
            if missing:
                raise ValueError(trans(
                    f"Missing sheets: {', '.join(missing)}",
                    f"برگه‌های زیر در فایل یافت نشد: {', '.join(missing)}"
                ))

            codeframe_df = pd.read_excel(excel_data, sheet_name="codeframe")
            question_df = pd.read_excel(excel_data, sheet_name="question")
            data_df = pd.read_excel(excel_data, sheet_name="data")

            # Validate columns
            if not all(col in codeframe_df.columns for col in ["QID", "CID", "Tag"]):
                raise ValueError(trans(
                    "The 'codeframe' sheet is missing required columns: QID, CID, Tag.",
                    "برگهٔ codeframe ستون‌های مورد نیاز QID، CID و Tag را ندارد."
                ))
            if 'Description' not in codeframe_df.columns:
                codeframe_df['Description'] = ''
            if not all(col in question_df.columns for col in ["QID", "Question"]):
                raise ValueError(trans(
                    "The 'question' sheet is missing required columns: QID, Question.",
                    "برگهٔ question ستون‌های مورد نیاز QID و Question را ندارد."
                ))
            if "ID" not in data_df.columns:
                raise ValueError(trans(
                    "The 'data' sheet is missing required column: ID.",
                    "برگهٔ data ستون مورد نیاز ID را ندارد."
                ))
        except Exception as e:
            context['errors'] = [str(e)]
            return render(request, 'coding.html', context)

        # Helper to parse API output (from IR9.py)
        def parse_output(output: str, qid: str) -> pd.DataFrame:
            parts = output.strip().split(';')
            data = []
            max_codes = 0
            for part in parts:
                if not part.strip():
                    continue
                items = part.strip().split(',')
                if len(items) < 2:
                    continue
                id_val = items[0].strip()
                codes = [code.strip() for code in items[1:] if code.strip()]
                data.append((id_val, codes))
                max_codes = max(max_codes, len(codes))
            if not data:
                return pd.DataFrame()
            columns = ['ID'] + [f'{qid}_{i+1}' for i in range(max_codes)]
            df_parsed = pd.DataFrame(columns=columns)
            for id_val, codes in data:
                row = {'ID': pd.to_numeric(id_val, errors='coerce')}
                for i, code in enumerate(codes):
                    row[f'{qid}_{i+1}'] = code
                df_parsed = pd.concat([df_parsed, pd.DataFrame([row])], ignore_index=True)
            return df_parsed.dropna(subset=['ID'])

        # Unique QIDs to process
        unique_qids = question_df['QID'].dropna().unique().tolist()
        results: dict[str, dict[str, str]] = {}
        fail_qids: list[str] = []
        dfs: list[pd.DataFrame] = []
        processed_qids: list[str] = []

        # Loop through each QID and fetch codes via API
        for qid in unique_qids:
            question_text = question_df.loc[question_df['QID'] == qid, 'Question'].iloc[0]
            # Compose options
            options_df = codeframe_df[codeframe_df['QID'] == qid][['CID', 'Tag', 'Description']]
            options_str = '\n'.join([f"{row['CID']} - {row['Tag']} - {row['Description']}" for _, row in options_df.iterrows()])
            # Prepare responses
            if qid in data_df.columns:
                responses_df = data_df[['ID', qid]].dropna(subset=[qid])
                responses_str = '\n'.join([f"{row['ID']} - {row[qid]}" for _, row in responses_df.iterrows()])
            else:
                responses_str = ''
            # Compose Farsi prompt (as in IR9.py)
            prompt = f"""
من یک پروژه تحقیقات بازار در حوزه {question_domain} انجام می دهم که شامل سوال زیر است: 

{question_text} (کاربر می تواند چند گزینه را انتخاب کند) 

گزینه ها(به فرمت : کد گزینه - عنوان گزینه - توضیحات): 

{options_str} 

پاسخ های کاربران را کامل بررسی کن و به هر کدام از سطرها، حداقل ۱ دسته اختصاص بده.

در نهایت خروجی را به این صورت به من تحویل بده که ابتدا آیدی کاربر را بنویس، سپس علامت «،» قرار بده و کد دسته‌های اختصاص یافته به آن آیدی را بنویس به طوری که با کمک "," از یکدیگر جدا کن. پس از پایان یافتن دسته‌های اختصاص یافته، علامت ";" بگذار و آیدی بعدی را بنویس و به شکل قبل دسته های اختصاص یافته به آن آیدی را مشخص کن. سپس خروجی را بدون توضیحات اضافی برای من همینجا تایپ کن.

دسته بندی را برای تک تک پاسخ های کاربران انجام بده و به من خروجی بده.
دسته بندی را برای تک تک پاسخ های کاربران انجام بده و به من خروجی بده. 

پاسخ کاربران(به فرمت : آیدی کاربر - پاسخ کاربر): 

{responses_str} 
"""
            # Prepare payload
            api_payload = {
                "model": "grok-4",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 2000
            }
            retries = 0
            max_retries = 6
            output = ""
            success = False
            while not success and retries < max_retries:
                try:
                    api_response = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=api_payload)
                    api_response.raise_for_status()
                    if 'application/json' in api_response.headers.get('Content-Type', ''):
                        response_json = api_response.json()
                        output = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        output = api_response.text
                        if '<!doctype' in output.lower():
                            output = "Forbidden HTML response"
                    success = True
                except (requests.exceptions.RequestException, json.JSONDecodeError):
                    retries += 1
                    if retries < max_retries:
                        time.sleep(10)
            if not success or not output or 'Forbidden' in output or 'API error' in output:
                fail_qids.append(qid)
                continue
            df_parsed = parse_output(output, qid)
            if df_parsed.empty:
                fail_qids.append(qid)
                continue
            results[qid] = {'prompt': prompt, 'output': output}
            dfs.append(df_parsed)
            processed_qids.append(qid)

        # After processing all QIDs
        if not dfs:
            context['errors'] = [trans('No valid data processed.', 'هیچ دادهٔ معتبری پردازش نشد.')]
            return render(request, 'coding.html', context)

        # Merge dataframes on ID (outer join)
        merged_df = reduce(lambda left, right: pd.merge(left, right, on='ID', how='outer'), dfs)
        merged_df = merged_df.sort_values('ID').reset_index(drop=True)

        # Build codeframe summary
        df_codeframe = pd.DataFrame(columns=['QID', 'Code', 'Tag', 'Tag_en', 'Count', 'Ratio'])
        total_ids = len(merged_df['ID'].unique()) if not merged_df.empty else 0
        for i, qid in enumerate(processed_qids):
            qid_df = dfs[i]
            qid_cols = [col for col in qid_df.columns if col.startswith(f'{qid}_')]
            melted = pd.melt(qid_df, id_vars=['ID'], value_vars=qid_cols, value_name='Code')
            melted['Code'] = melted['Code'].astype(str).str.strip()
            melted = melted[melted['Code'] != ''].dropna(subset=['Code'])
            melted = melted[pd.to_numeric(melted['Code'], errors='coerce').notna()]
            code_counts = melted['Code'].value_counts().reset_index()
            code_counts.columns = ['Code', 'Count']
            code_counts['QID'] = qid
            code_counts['Ratio'] = code_counts['Count'] / total_ids if total_ids > 0 else 0
            # Map code to Tag from codeframe_df
            code_counts['Tag'] = code_counts['Code'].apply(
                lambda code: codeframe_df.loc[codeframe_df['CID'] == code, 'Tag'].iloc[0] if not codeframe_df.loc[codeframe_df['CID'] == code].empty else ''
            )
            code_counts['Tag_en'] = ''
            code_counts = code_counts[['QID', 'Code', 'Tag', 'Tag_en', 'Count', 'Ratio']]
            df_codeframe = pd.concat([df_codeframe, code_counts], ignore_index=True)

        # Build binary sheet
        binary_df = pd.DataFrame({'ID': merged_df['ID'].unique()}).sort_values('ID').reset_index(drop=True)
        for i, qid in enumerate(processed_qids):
            qid_df = dfs[i]
            qid_cols = [col for col in qid_df.columns if col.startswith(f'{qid}_')]
            melted = pd.melt(qid_df, id_vars=['ID'], value_vars=qid_cols, value_name='Code')
            melted['Code'] = melted['Code'].astype(str).str.strip()
            melted = melted[melted['Code'] != ''].dropna(subset=['Code'])
            melted = melted[pd.to_numeric(melted['Code'], errors='coerce').notna()]
            unique_codes = melted['Code'].unique()
            for code in unique_codes:
                col_name = f"{qid}-{code}"
                binary_df[col_name] = binary_df['ID'].apply(
                    lambda id_val, c=code: 1 if not melted[(melted['ID'] == id_val) & (melted['Code'] == c)].empty else pd.NA
                )

        # Create Excel file in memory
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            merged_df.to_excel(writer, sheet_name='triple', index=False)
            df_codeframe.to_excel(writer, sheet_name='codeframe', index=False)
            binary_df.to_excel(writer, sheet_name='binary', index=False)
        excel_buffer.seek(0)
        excel_b64 = base64.b64encode(excel_buffer.read()).decode('utf-8')
        # Provide download link via data URI
        excel_filename = f"processed_data_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{project_name}.xlsx"
        excel_download_uri = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_b64}"

        # Build bar chart
        chart_uri = None
        if not df_codeframe.empty:
            pivot_df = df_codeframe.pivot_table(index='QID', columns='Code', values='Count', fill_value=0)
            fig, ax = plt.subplots(figsize=(10, 5))
            pivot_df.plot(kind='bar', ax=ax)
            ax.set_title('Count by QID and Code')
            ax.set_xlabel('QID')
            ax.set_ylabel('Count')
            ax.legend(title='Code', bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            chart_b64 = base64.b64encode(buf.read()).decode('utf-8')
            chart_uri = f"data:image/png;base64,{chart_b64}"
            plt.close(fig)

        # Convert DataFrames to HTML for display
        df_triple_html = merged_df.to_html(index=False, classes='table table-striped')
        df_codeframe_html = df_codeframe.to_html(index=False, classes='table table-striped')
        df_binary_html = binary_df.to_html(index=False, classes='table table-striped')

        # Update context with results
        context.update({
            'df_triple_html': df_triple_html,
            'df_codeframe_html': df_codeframe_html,
            'df_binary_html': df_binary_html,
            'excel_download_uri': excel_download_uri,
            'excel_filename': excel_filename,
            'chart_uri': chart_uri,
            'processed_qids': processed_qids,
            'fail_qids': fail_qids,
        })

        return render(request, 'coding.html', context)

    # GET request: render page with empty form
    return render(request, 'coding.html', context)