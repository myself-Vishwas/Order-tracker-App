import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Mali's Cookies",
    page_icon="🍪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Product list ──────────────────────────────────────────────────────────────
PRODUCTS = [
    "Wheat (Jaggery)",
    "Wheat (Sugar)",
    "Nachni (Jaggery)",
    "Nachni (Sugar)",
    "Roat",
    "Suzberry",
    "Chocolate",
    "Pista",
    "Orange",
    "Pedha",
    "Yellow Pedha",
    "Maida Mix (200gm)",
    "Majoori Wheat",
    "Majoori Roat",
    "Majoori Nachni",
    "Kajuu",
]

# ── Mobile-first CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container {
    padding: 1.2rem 1rem 2rem 1rem !important;
    max-width: 480px !important;
    margin: auto;
  }
  .app-header {
    background: #1a56db;
    color: white;
    border-radius: 14px;
    padding: 18px 20px 14px;
    margin-bottom: 22px;
    text-align: center;
  }
  .app-header img {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid rgba(255,255,255,0.4);
    margin-bottom: 10px;
    display: block;
    margin-left: auto;
    margin-right: auto;
  }
  .app-header h1 { font-size: 1.5rem; margin: 0; letter-spacing: -0.3px; }
  .app-header p  { font-size: 0.82rem; margin: 4px 0 0; opacity: 0.82; }
  .field-label {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #374151;
    margin-bottom: 2px;
  }
  .qty-row { display: flex; gap: 10px; }
  input, textarea, select,
  .stTextInput input,
  .stNumberInput input,
  .stTextArea textarea,
  .stDateInput input,
  .stSelectbox div[data-baseweb="select"] {
    font-size: 1rem !important;
    border-radius: 10px !important;
    border: 1.5px solid #d1d5db !important;
    min-height: 48px !important;
  }
  .stTextArea textarea { min-height: 90px !important; }
  /* Quantity unit badge */
  .unit-label {
    display: inline-block;
    background: #e0e7ff;
    color: #3730a3;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 6px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .stButton > button {
    width: 100% !important;
    background: #1a56db !important;
    color: white !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    padding: 14px !important;
    border: none !important;
    margin-top: 8px;
  }
  .stButton > button:hover  { background: #1648c0 !important; }
  .stButton > button:active { background: #1240b0 !important; }
  .stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #f3f4f6;
    border-radius: 12px;
    padding: 4px;
    margin-bottom: 16px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 8px 0;
  }
  .success-banner {
    background: #ecfdf5;
    border: 1.5px solid #6ee7b7;
    color: #065f46;
    border-radius: 12px;
    padding: 14px 16px;
    font-weight: 600;
    font-size: 0.95rem;
    margin-top: 10px;
  }
  .setup-warning {
    background: #fef3c7;
    border: 1.5px solid #f59e0b;
    border-radius: 12px;
    padding: 16px;
    color: #92400e;
    font-size: 0.93rem;
    line-height: 1.6;
  }
  .order-card {
    background: white;
    border: 1.5px solid #e5e7eb;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .order-card .order-date {
    font-size: 0.78rem;
    color: #6b7280;
    margin-bottom: 4px;
  }
  .order-card .product-name {
    font-size: 1.1rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 6px;
  }
  .order-card .badges { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
  .badge-blue {
    display: inline-block;
    background: #eff6ff;
    color: #1d4ed8;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
  }
  .badge-green {
    display: inline-block;
    background: #f0fdf4;
    color: #15803d;
    font-size: 0.82rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
  }
  .order-card .notes-text {
    font-size: 0.88rem;
    color: #4b5563;
    font-style: italic;
    margin-top: 4px;
  }
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Logo loader ───────────────────────────────────────────────────────────────
def get_logo_html() -> str:
    logo_path = Path("logo.png")
    if logo_path.exists():
        data = base64.b64encode(logo_path.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{data}" alt="Logo">'
    return '<div style="font-size:3rem;margin-bottom:6px;">🍪</div>'


# ── Secrets check ─────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def secrets_configured() -> bool:
    try:
        _ = st.secrets["gcp_service_account"]
        _ = st.secrets["SHEET_ID"]
        return True
    except Exception:
        return False

def show_setup_warning():
    st.markdown("""
    <div class="setup-warning">
      <b>⚙️ Setup not complete yet</b><br><br>
      Google Sheets credentials haven't been added to Streamlit.<br><br>
      <b>To fix this:</b><br>
      1. Click <b>Manage app</b> (bottom right of screen)<br>
      2. Click ⋮ menu → <b>Settings</b> → <b>Secrets</b><br>
      3. Paste your credentials block and click <b>Save</b>
    </div>
    """, unsafe_allow_html=True)


# ── Google Sheets connection ──────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_sheet():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["SHEET_ID"]).sheet1


def append_order(delivery_date, product, packets, kg, notes):
    sheet = get_sheet()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_rows = sheet.get_all_values()
    data_rows = [r for r in all_rows[2:] if any(cell.strip() for cell in r)]
    next_sr = len(data_rows) + 1
    # Columns: Sr.No | Timestamp | Delivery Date | Product Name | No. of Packets | KG | Notes
    sheet.append_row(
        [next_sr, timestamp, delivery_date, product, packets, kg, notes],
        value_input_option="USER_ENTERED",
    )
    return next_sr, timestamp


@st.cache_data(ttl=30, show_spinner=False)
def load_orders() -> pd.DataFrame:
    sheet = get_sheet()
    all_values = sheet.get_all_values()
    if len(all_values) < 3:
        return pd.DataFrame(columns=["Sr. No", "Timestamp", "Delivery Date",
                                     "Product Name", "No. of Packets", "KG", "Notes"])
    headers = all_values[1]
    data = [r for r in all_values[2:] if any(cell.strip() for cell in r)]
    if not data:
        return pd.DataFrame(columns=headers)
    df = pd.DataFrame(data, columns=headers)
    return df.iloc[::-1].reset_index(drop=True)


# ── Email notification ────────────────────────────────────────────────────────
def send_order_email(sr_no, timestamp, delivery_date, product, packets, kg, notes):
    try:
        sender    = st.secrets["EMAIL_SENDER"]
        password  = st.secrets["EMAIL_PASSWORD"]
        recipient = st.secrets["EMAIL_RECIPIENT"]
    except Exception:
        return False

    subject = f"🍪 New Order #{sr_no} — {product}"
    body = f"""
🍪 New Order Received — Mali's Cookies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Order No      : #{sr_no}
🕐 Logged At     : {timestamp}
🚚 Deliver By    : {delivery_date}
🍪 Product       : {product}
📦 No. of Packets: {packets}
⚖️  KG            : {kg}
📝 Notes         : {notes if notes else "—"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
View all orders → https://order-tracker-app-vx2f29k26i86h9nrwyaatt.streamlit.app/
    """.strip()

    try:
        msg = MIMEMultipart()
        msg["From"]    = sender
        msg["To"]      = recipient
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        return True
    except Exception:
        return False


# ── App header with logo ──────────────────────────────────────────────────────
logo_html = get_logo_html()
st.markdown(f"""
<div class="app-header">
  {logo_html}
  <h1>Mali's Cookies</h1>
  <p>Order Entry · Track Deliveries</p>
</div>
""", unsafe_allow_html=True)


# ── Two-tab layout ────────────────────────────────────────────────────────────
tab_enter, tab_view = st.tabs(["➕  New Order", "📋  View Orders"])


# ── TAB 1 — Order entry ───────────────────────────────────────────────────────
with tab_enter:
    if not secrets_configured():
        show_setup_warning()
    else:
        with st.form("order_form", clear_on_submit=True):

            st.markdown('<p class="field-label">Delivery Date</p>', unsafe_allow_html=True)
            delivery_date = st.date_input(
                label="delivery_date",
                value=date.today(),
                label_visibility="collapsed",
                min_value=date.today(),
            )

            st.markdown('<p class="field-label">Product Name</p>', unsafe_allow_html=True)
            product_name = st.selectbox(
                label="product_name",
                options=PRODUCTS,
                label_visibility="collapsed",
            )

            st.markdown('<p class="field-label">Quantity</p>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<span class="unit-label">📦 No. of Packets</span>', unsafe_allow_html=True)
                no_of_packets = st.number_input(
                    label="no_of_packets",
                    min_value=0,
                    step=1,
                    value=0,
                    label_visibility="collapsed",
                )
            with col2:
                st.markdown('<span class="unit-label">⚖️ KG</span>', unsafe_allow_html=True)
                kg = st.number_input(
                    label="kg",
                    min_value=0.0,
                    step=0.5,
                    value=0.0,
                    format="%.1f",
                    label_visibility="collapsed",
                )

            st.markdown('<p class="field-label">Notes</p>', unsafe_allow_html=True)
            notes = st.text_area(
                label="notes",
                placeholder="Special instructions, packaging, urgency…",
                label_visibility="collapsed",
            )

            submitted = st.form_submit_button("Save Order →")

        if submitted:
            if no_of_packets == 0 and kg == 0.0:
                st.error("⚠️ Please enter at least No. of Packets or KG.")
            else:
                with st.spinner("Saving order…"):
                    try:
                        sr_no, timestamp = append_order(
                            str(delivery_date),
                            product_name,
                            int(no_of_packets),
                            float(kg),
                            notes.strip(),
                        )
                        load_orders.clear()
                        email_sent = send_order_email(
                            sr_no, timestamp, str(delivery_date),
                            product_name, int(no_of_packets), float(kg), notes.strip()
                        )
                        email_note = " · 📧 Notification sent!" if email_sent else ""
                        st.markdown(
                            f'<div class="success-banner">✅ Order #{sr_no} saved!{email_note}</div>',
                            unsafe_allow_html=True,
                        )
                    except Exception as e:
                        st.error(f"❌ Failed to save: {e}")


# ── TAB 2 — View orders ───────────────────────────────────────────────────────
with tab_view:
    if not secrets_configured():
        show_setup_warning()
    else:
        with st.spinner("Loading orders…"):
            try:
                df = load_orders()
                if df.empty:
                    st.info("No orders yet. Add one in the 'New Order' tab.")
                else:
                    st.caption(f"{len(df)} order(s) · auto-refreshes every 30 s")
                    for _, row in df.iterrows():
                        notes_html = (
                            f'<div class="notes-text">💬 {row.get("Notes", "")}</div>'
                            if str(row.get("Notes", "")).strip()
                            else ""
                        )
                        packets_val = row.get("No. of Packets", "0")
                        kg_val      = row.get("KG", "0")
                        st.markdown(f"""
                        <div class="order-card">
                          <div class="order-date">🚚 Deliver by {row.get('Delivery Date','')} &nbsp;·&nbsp; {row.get('Timestamp','')}</div>
                          <div class="product-name">#{row.get('Sr. No','')} &nbsp;{row.get('Product Name','')}</div>
                          <div class="badges">
                            <span class="badge-blue">📦 {packets_val} Packets</span>
                            <span class="badge-green">⚖️ {kg_val} KG</span>
                          </div>
                          {notes_html}
                        </div>
                        """, unsafe_allow_html=True)
                    with st.expander("Show full data table"):
                        st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"❌ Could not load orders: {e}")
                st.info("Please check your secrets are correctly configured.")
