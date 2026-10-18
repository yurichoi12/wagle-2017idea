import html
import itertools
import math
import json
import urllib.parse
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="이벤트팀 아이디어 모음", page_icon="💡", layout="centered")

# setup_idea_sheet.py 실행 후 터미널에 출력된 SPREADSHEET_ID를 여기에 붙여넣어주세요.
SPREADSHEET_ID = "여기에_setup_idea_sheet.py가_출력한_ID를_붙여넣으세요"

# 전체 UI 스타일링 (와글 북큐 검색기와 같은 톤의 보라색 테마)
st.markdown("""
    <style>
    div[data-testid="InputInstructions"], div[data-testid="stInputInstruction"] {
        display: none !important;
    }
    div.stTextInput > div > div {
        background-color: #e8f0fe !important;
        border-radius: 12px !important;
        border: 2px solid #3f6fd1 !important;
        height: 50px !important;
    }
    div.stTextInput > div > div > input {
        height: 50px !important;
        font-size: 18px;
        background-color: transparent !important;
        color: #2c3e50 !important;
        border: none !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    div.stTextInput > div > div > input:focus {
        box-shadow: none !important;
    }
    .stButton > button {
        height: 50px !important;
        border-radius: 12px !important;
        border: 2px solid #3f6fd1 !important;
        background-color: #ffffff !important;
        color: #3f6fd1 !important;
        font-weight: bold !important;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #e8f0fe !important;
        border-color: #3f6fd1 !important;
        color: #3f6fd1 !important;
    }
    .stButton > button:disabled {
        opacity: 0.4 !important;
    }
    .page-option-link {
        color: #666666;
        text-decoration: none;
        font-size: 14px;
        margin-left: 10px;
        cursor: pointer;
    }
    .page-option-link:hover {
        color: #3f6fd1;
        text-decoration: underline;
    }
    .page-option-selected {
        color: #3f6fd1;
        font-weight: bold;
        font-size: 14px;
        margin-left: 10px;
    }
    .st-key-home_btn_wrap {
        display: flex;
        justify-content: flex-end;
        margin-top: 4px;
    }
    .st-key-home_btn_wrap .stButton > button {
        height: auto !important;
        min-height: unset !important;
        width: auto !important;
        padding: 3px 10px !important;
        font-size: 11px !important;
        border-width: 1px !important;
        border-radius: 6px !important;
    }

    /* ===== 페이지 이동 네비게이션 (모바일에서도 한 줄 유지) ===== */
    .page-nav-row {
        display: flex;
        flex-wrap: nowrap;
        align-items: center;
        justify-content: center;
        gap: 6px;
        width: 100%;
    }
    .page-nav-btn {
        flex: 0 0 auto;
        display: inline-block;
        padding: 6px 8px;
        border: 1.5px solid #3f6fd1;
        border-radius: 8px;
        color: #3f6fd1;
        font-size: 12px;
        font-weight: bold;
        text-decoration: none;
        text-align: center;
        white-space: nowrap;
        background-color: #ffffff;
    }
    .page-nav-btn:hover {
        background-color: #e8f0fe;
    }
    .page-nav-btn.page-nav-disabled {
        color: #cccccc;
        border-color: #e5e5e5;
        cursor: default;
        background-color: #fafafa;
    }
    .page-nav-info {
        flex: 0 0 auto;
        font-size: 13px;
        font-weight: bold;
        color: #2c3e50;
        white-space: nowrap;
        padding: 0 6px;
    }
    @media (max-width: 480px) {
        .page-nav-btn {
            padding: 6px 6px;
            font-size: 11px;
        }
        .page-nav-info {
            font-size: 12px;
            padding: 0 3px;
        }
    }

    /* ===== 아이디어 카드 그리드 ===== */
    .idea-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin: 10px 0 18px 0;
    }
    .idea-card {
        background-color: #ffffff;
        border: 1px solid #ececec;
        border-radius: 10px;
        padding: 10px 10px 12px 10px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    }
    .idea-card .card-toggle {
        display: none;
    }
    .idea-card .card-nickname {
        font-size: 12px;
        font-weight: bold;
        color: #3f6fd1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 4px;
    }
    .idea-card .card-links {
        margin-bottom: 4px;
    }
    .idea-card .card-links:empty {
        display: none;
    }
    .idea-card a.idea-link {
        display: inline-block;
        color: #3f6fd1;
        text-decoration: underline;
        font-size: 11px;
    }
    .idea-card .card-body-wrap {
        display: block;
        cursor: pointer;
    }
    .idea-card .card-body-text {
        font-size: 13px;
        color: #2c3e50;
        line-height: 1.45;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
        word-break: break-word;
        white-space: pre-wrap;
    }
    .idea-card .more-toggle {
        display: block;
        text-align: center;
        font-size: 9.5px;
        color: #3f6fd1;
        margin-top: 5px;
        opacity: 0.8;
    }
    .idea-card .less-toggle {
        display: none;
        text-align: center;
        font-size: 9.5px;
        color: #3f6fd1;
        margin-top: 8px;
        padding-top: 6px;
        border-top: 1px dashed #d7e3fb;
        cursor: pointer;
    }
    .idea-card .card-toggle:checked ~ .card-body-wrap .card-body-text {
        -webkit-line-clamp: unset;
        display: block;
    }
    .idea-card .card-toggle:checked ~ .card-body-wrap .more-toggle {
        display: none;
    }
    .idea-card .card-toggle:checked ~ .less-toggle {
        display: block;
    }
    .idea-card .card-date {
        font-size: 9.5px;
        color: #aaaaaa;
        margin-top: 6px;
    }
    @media (max-width: 480px) {
        .idea-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
""", unsafe_allow_html=True)


def get_gspread_client():
    SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    if "gcp_service_account" in st.secrets:
        raw = st.secrets["gcp_service_account"]
        if isinstance(raw, str):
            creds_dict = json.loads(raw)
        else:
            creds_dict = dict(raw)
            if "private_key" in creds_dict and isinstance(creds_dict["private_key"], str):
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    elif "gcp_json_str" in st.secrets:
        raw = st.secrets["gcp_json_str"]
        if isinstance(raw, str):
            creds_dict = json.loads(raw)
        else:
            creds_dict = dict(raw)
    else:
        st.error("Secrets에서 인증 정보를 찾지 못했습니다.")
        st.stop()
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)


def clean_name(raw_name):
    if not raw_name:
        return "익명"
    name = raw_name.strip()
    for delimiter in ["-", ":", "_", " "]:
        if delimiter in name:
            name = name.split(delimiter)[0]
    return name.strip() if name.strip() else "익명"


def format_sheet_updated_time(iso_str):
    """구글 시트 파일의 마지막 수정 시각(Drive API의 modifiedTime, UTC)을
    한국 시간(KST) 기준 'yyyy.mm.dd. HH:MM' 형태로 변환합니다."""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        kst = dt.astimezone(timezone(timedelta(hours=9)))
        return kst.strftime("%Y.%m.%d. %H:%M")
    except Exception:
        return ""


def clean_idea_body(content):
    """'#아이디어' 태그 자체는 카드 본문에서 보여줄 필요가 없으니 지워줍니다."""
    if not content:
        return ""
    return content.replace("#아이디어", "").strip()


_card_id_counter = itertools.count()


def render_idea_card(item):
    card_id = f"card-toggle-{next(_card_id_counter)}"
    raw_sender = item.get("보낸사람", "익명")
    display_name = html.escape(clean_name(raw_sender))
    date_str = html.escape(item.get("작성일시", ""))
    body_safe = html.escape(clean_idea_body(item.get("내용", "")))

    link = item.get("링크", "")
    links_html = ""
    if link:
        for l in link.split("\n"):
            l = l.strip()
            if l:
                l_safe = html.escape(l, quote=True)
                links_html += (
                    f'<a href="{l_safe}" target="_blank" rel="noopener noreferrer" '
                    f'class="idea-link" onclick="event.stopPropagation()">🔗 링크 이동</a>'
                )

    return (
        '<div class="idea-card">'
        f'<input type="checkbox" class="card-toggle" id="{card_id}">'
        f'<div class="card-nickname">👤 {display_name}</div>'
        f'<div class="card-links">{links_html}</div>'
        f'<label for="{card_id}" class="card-body-wrap">'
        f'<div class="card-body-text">{body_safe}</div>'
        '<span class="more-toggle">▼ 더보기</span>'
        '</label>'
        f'<label for="{card_id}" class="less-toggle">▲ 접기</label>'
        f'<div class="card-date">{date_str}</div>'
        '</div>'
    )


def render_idea_grid(items):
    cards = "".join(render_idea_card(item) for item in items)
    st.markdown(f'<div class="idea-grid">{cards}</div>', unsafe_allow_html=True)


@st.cache_data(ttl=60)
def load_data():
    client = get_gspread_client()
    doc = client.open_by_key(SPREADSHEET_ID)
    sheet = doc.worksheets()[0]
    data = sheet.get_all_values()

    # 구글 시트 "파일" 자체의 마지막 수정 시각(Drive API modifiedTime)을 함께 가져옵니다.
    sheet_updated_raw = ""
    try:
        drive_resp = client.http_client.session.get(
            f"https://www.googleapis.com/drive/v3/files/{SPREADSHEET_ID}",
            params={"fields": "modifiedTime"},
            timeout=5,
        )
        if drive_resp.status_code == 200:
            sheet_updated_raw = drive_resp.json().get("modifiedTime", "")
    except Exception:
        sheet_updated_raw = ""

    if not data:
        return [], sheet_updated_raw
    headers = data[0]
    rows = data[1:]
    parsed_data = []
    for row in rows:
        item = {}
        for i, h in enumerate(headers):
            item[h] = row[i] if i < len(row) else ""
        parsed_data.append(item)
    parsed_data.sort(key=lambda x: x.get("작성일시", ""), reverse=True)
    return parsed_data, sheet_updated_raw


st.title("💡 이벤트팀 아이디어 모음")
st.caption("모임원들이 공유한 #아이디어 메시지를 모아모아! (2026.10.1 이후)")

query_params = st.query_params
if "per_page" in query_params:
    try:
        val = int(query_params["per_page"])
        if val in [15, 18, 21, 24]:
            st.session_state.items_per_page = val
    except:
        pass
if "page" in query_params:
    try:
        pval = int(query_params["page"])
        if pval >= 1:
            st.session_state.page_num = pval
    except:
        pass


def clear_search():
    st.session_state.search_box = ""


try:
    items, sheet_updated_raw = load_data()

    search_query = st.text_input(
        "🔍 #아이디어 통합 검색",
        placeholder="작성자, 내용 입력",
        label_visibility="collapsed",
        key="search_box"
    )

    filtered_items = items
    if search_query:
        query = search_query.lower()
        filtered_items = [
            item for item in items
            if query in item.get("작성일시", "").lower()
            or query in clean_name(item.get("보낸사람", "")).lower()
            or query in item.get("내용", "").lower()
            or query in item.get("링크", "").lower()
        ]

    total_count = len(filtered_items)

    if "items_per_page" not in st.session_state:
        st.session_state.items_per_page = 15
    if "page_num" not in st.session_state:
        st.session_state.page_num = 1

    st.write("")

    latest_update_str = format_sheet_updated_time(sheet_updated_raw)

    col_count_text, col_per_page = st.columns([2, 3])
    with col_count_text:
        count_html = f"<div style='padding-top: 12px;'><b>총 {total_count}건의 #아이디어 메시지</b>"
        if latest_update_str:
            count_html += f'<div style="font-size: 11px; color: #999999; margin-top: 2px;">최근 업데이트: {html.escape(latest_update_str)}</div>'
        count_html += "</div>"
        st.markdown(count_html, unsafe_allow_html=True)
    with col_per_page:
        current_per_page = st.session_state.items_per_page
        options_html = "<div style='text-align: right; padding-top: 4px;'><span style='font-size: 11px; color: #888888; margin-right: 4px;'>한 페이지에 표시할 카드 개수:</span>"
        for opt in [15, 18, 21, 24]:
            if current_per_page == opt:
                options_html += f"<span class='page-option-selected'>{opt}</span>"
            else:
                options_html += f"<a href='?per_page={opt}' target='_self' class='page-option-link'>{opt}</a>"
        options_html += "</div>"
        st.markdown(options_html, unsafe_allow_html=True)
        if search_query:
            with st.container(key="home_btn_wrap"):
                st.button("🏠 전체 목록으로", key="back_home_btn", on_click=clear_search)

    items_per_page = st.session_state.items_per_page

    st.write("")

    if total_count > 0:
        total_pages = math.ceil(total_count / items_per_page)

        if "prev_search" not in st.session_state:
            st.session_state.prev_search = search_query
        if st.session_state.prev_search != search_query:
            st.session_state.page_num = 1
            st.session_state.prev_search = search_query

        if st.session_state.page_num > total_pages:
            st.session_state.page_num = max(1, total_pages)

        current_page = st.session_state.page_num
        start_idx = (current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = filtered_items[start_idx:end_idx]

        render_idea_grid(page_items)

        if total_pages > 1:
            st.write("")
            if current_page > 1:
                first_btn = '<a href="?page=1" target="_self" class="page-nav-btn">« 맨앞</a>'
                prev_btn = f'<a href="?page={current_page - 1}" target="_self" class="page-nav-btn">‹ 이전</a>'
            else:
                first_btn = '<span class="page-nav-btn page-nav-disabled">« 맨앞</span>'
                prev_btn = '<span class="page-nav-btn page-nav-disabled">‹ 이전</span>'
            if current_page < total_pages:
                next_btn = f'<a href="?page={current_page + 1}" target="_self" class="page-nav-btn">다음 ›</a>'
                last_btn = f'<a href="?page={total_pages}" target="_self" class="page-nav-btn">맨뒤 »</a>'
            else:
                next_btn = '<span class="page-nav-btn page-nav-disabled">다음 ›</span>'
                last_btn = '<span class="page-nav-btn page-nav-disabled">맨뒤 »</span>'
            page_info = f'<span class="page-nav-info">{current_page} / {total_pages}</span>'
            st.markdown(
                f'<div class="page-nav-row">{first_btn}{prev_btn}{page_info}{next_btn}{last_btn}</div>',
                unsafe_allow_html=True
            )

except Exception as e:
    st.error(f"구글 시트 데이터를 불러오는 중 오류가 발생했습니다: {e}")
