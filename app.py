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
    "Wheat (Jaggery)", "Wheat (Sugar)", "Nachni (Jaggery)", "Nachni (Sugar)",
    "Roat", "Suzberry", "Chocolate", "Pista", "Orange", "Pedha",
    "Yellow Pedha", "Maida Mix (200gm)", "Majoori Wheat",
    "Majoori Roat", "Majoori Nachni", "Kajuu",
]

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container {
    padding: 1.2rem 1rem 2rem 1rem !important;
    max-width: 520px !important;
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
    width: 80px; height: 80px;
    border-radius: 50%; object-fit: cover;
    border: 3px solid rgba(255,255,255,0.4);
    margin-bottom: 10px;
    display: block; margin-left: auto; margin-right: auto;
  }
  .app-header h1 { font-size: 1.5rem; margin: 0; }
  .app-header p  { font-size: 0.82rem; margin: 4px 0 0; opacity: 0.82; }
  .field-label {
    font-size: 0.78rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.06em;
    color: #374151; margin-bottom: 2px;
  }
  .unit-label {
    display: inline-block;
    background: #e0e7ff; color: #3730a3;
    font-size: 0.72rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px;
    margin-bottom: 4px;
    text-transform: uppercase;
  }
  .unit-label-green {
    display: inline-block;
    background: #f0fdf4; color: #15803d;
    font-size: 0.72rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px;
    margin-bottom: 4px;
    text-transform: uppercase;
  }
  .unit-label-orange {
    display: inline-block;
    background: #fff7ed; color: #c2410c;
    font-size: 0.72rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px;
    margin-bottom: 4px;
    text-transform: uppercase;
  }
  input, textarea, select,
  .stTextInput input, .stNumberInput input,
  .stTextArea textarea, .stDateInput input {
    font-size: 1rem !important;
    border-radius: 10px !important;
    border: 1.5px solid #d1d5db !important;
    min-height: 44px !important;
  }
  .stTextArea textarea { min-height: 80px !important; }
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
  .stButton > button:hover { background: #1648c0 !important; }
  .stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: #f3f4f6;
    border-radius: 12px; padding: 4px; margin-bottom: 16px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 9px; font-weight: 600; font-size: 0.9rem; padding: 8px 0;
  }
  .setup-warning {
    background: #fef3c7; border: 1.5px solid #f59e0b;
    border-radius: 12px; padding: 16px;
    color: #92400e; font-size: 0.93rem; line-height: 1.6;
  }
  #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Logo ──────────────────────────────────────────────────────────────────────
def get_logo_html():
    p = Path("logo.png")
    if p.exists():
        data = base64.b64encode(p.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{data}" alt="Logo">'
    return '<div style="font-size:3rem;margin-bottom:6px;">🍪</div>'


# ── Secrets ───────────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def secrets_configured():
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
      Google Sheets credentials haven't been added.<br><br>
      1. Click <b>Manage app</b> (bottom right)<br>
      2. ⋮ → <b>Settings → Secrets</b><br>
      3. Paste credentials → <b>Save</b>
    </div>
    """, unsafe_allow_html=True)


# ── Sheets ────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_sheet():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES)
    return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"]).sheet1


def append_order(delivery_date, items, notes):
    """
    Save ONE row per order. Multiple products are pipe-separated.
    Sheet columns (Row 2 headers):
    Sr. No | Timestamp | Delivery Date | Products | No. of Packets | KG | Price | Notes
    """
    sheet     = get_sheet()
    timestamp = datetime.now().strftime("%d/%m/%Y - %H:%M:%S")
    all_rows  = sheet.get_all_values()
    data_rows = [r for r in all_rows[2:] if any(c.strip() for c in r)]
    next_sr   = len(data_rows) + 1

    products = " | ".join(i["product"]      for i in items)
    packets  = " | ".join(str(i["packets"]) for i in items)
    kgs      = " | ".join(str(i["kg"])      for i in items)
    prices   = " | ".join(str(i["price"])   for i in items)

    sheet.append_row(
        [next_sr, timestamp, str(delivery_date), products, packets, kgs, prices, notes],
        value_input_option="USER_ENTERED",
    )
    return next_sr, timestamp


@st.cache_data(ttl=30, show_spinner=False)
def load_orders():
    sheet      = get_sheet()
    all_values = sheet.get_all_values()
    if len(all_values) < 3:
        return []
    data = [r for r in all_values[2:] if any(c.strip() for c in r)]
    return list(reversed(data))   # newest first


# ── Email ─────────────────────────────────────────────────────────────────────
def send_order_email(sr_no, timestamp, delivery_date, items, notes):
    try:
        sender    = st.secrets["EMAIL_SENDER"]
        password  = st.secrets["EMAIL_PASSWORD"]
        recipient = st.secrets["EMAIL_RECIPIENT"]
    except Exception:
        return False
    lines = "\n".join(
        f"  {idx+1}. {i['product']} — {i['packets']} pkts | {i['kg']} KG | Rs.{i['price']}"
        for idx, i in enumerate(items)
    )
    body = f"""
New Order — Mali's Cookies
Order No   : #{sr_no}
Logged At  : {timestamp}
Deliver By : {delivery_date}

Items:
{lines}

Notes : {notes if notes else '—'}
View → https://order-tracker-app-vx2f29k26i86h9nrwyaatt.streamlit.app/
    """.strip()
    try:
        msg = MIMEMultipart()
        msg["From"] = sender; msg["To"] = recipient
        msg["Subject"] = f"New Order #{sr_no} ({len(items)} item{'s' if len(items)>1 else ''})"
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())
        return True
    except Exception:
        return False


# ── Session state ─────────────────────────────────────────────────────────────
if "num_items" not in st.session_state:
    st.session_state.num_items = 1


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
  {get_logo_html()}
  <h1>Mali's Cookies</h1>
  <p>Order Entry · Track Deliveries</p>
</div>
""", unsafe_allow_html=True)

tab_enter, tab_view = st.tabs(["➕  New Order", "📋  View Orders"])


# ════════════════════════════════════════════════════════════════
# TAB 1 — New Order
# ════════════════════════════════════════════════════════════════
with tab_enter:
    if not secrets_configured():
        show_setup_warning()
    else:
        st.markdown('<p class="field-label">Delivery Date</p>', unsafe_allow_html=True)
        delivery_date = st.date_input(
            "delivery_date", value=date.today(),
            min_value=date.today(), label_visibility="collapsed"
        )

        st.markdown('<p class="field-label">Products Ordered</p>', unsafe_allow_html=True)

        items_data = []
        for i in range(st.session_state.num_items):
            with st.container(border=True):
                st.markdown(f"**🛒 Item {i+1}**")

                prod = st.selectbox(
                    "Product", PRODUCTS,
                    key=f"prod_{i}"
                )

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown('<span class="unit-label">📦 Packets</span>', unsafe_allow_html=True)
                    pkts = st.number_input(
                        "Packets", min_value=0, step=1, value=0,
                        key=f"pkts_{i}", label_visibility="collapsed"
                    )
                with c2:
                    st.markdown('<span class="unit-label-green">⚖️ KG</span>', unsafe_allow_html=True)
                    kg = st.number_input(
                        "KG", min_value=0.0, step=0.5, value=0.0,
                        format="%.1f", key=f"kg_{i}", label_visibility="collapsed"
                    )
                with c3:
                    st.markdown('<span class="unit-label-orange">₹ Price</span>', unsafe_allow_html=True)
                    price = st.number_input(
                        "Price", min_value=0.0, step=1.0, value=0.0,
                        format="%.0f", key=f"price_{i}", label_visibility="collapsed"
                    )

                items_data.append({
                    "product": prod,
                    "packets": int(pkts),
                    "kg": float(kg),
                    "price": float(price),
                })

                if st.session_state.num_items > 1:
                    if st.button(f"✕ Remove Item {i+1}", key=f"remove_{i}"):
                        st.session_state.num_items -= 1
                        for k in [f"prod_{i}", f"pkts_{i}", f"kg_{i}", f"price_{i}"]:
                            st.session_state.pop(k, None)
                        st.rerun()

        col_add, _ = st.columns([1, 2])
        with col_add:
            if st.button("＋ Add Product"):
                st.session_state.num_items += 1
                st.rerun()

        st.markdown('<p class="field-label" style="margin-top:10px">Notes</p>', unsafe_allow_html=True)
        notes = st.text_area(
            "notes", placeholder="Special instructions, packaging, urgency…",
            label_visibility="collapsed"
        )

        if st.button("💾  Save Order →"):
            invalid = [i+1 for i, it in enumerate(items_data)
                       if it["packets"] == 0 and it["kg"] == 0.0]
            if invalid:
                st.error(f"⚠️ Item(s) {invalid}: enter Packets or KG.")
            else:
                with st.spinner("Saving…"):
                    try:
                        sr_no, timestamp = append_order(
                            str(delivery_date), items_data, notes.strip()
                        )
                        load_orders.clear()
                        email_sent = send_order_email(
                            sr_no, timestamp, str(delivery_date),
                            items_data, notes.strip()
                        )
                        for k in list(st.session_state.keys()):
                            if any(k.startswith(p) for p in ["prod_","pkts_","kg_","price_"]):
                                del st.session_state[k]
                        st.session_state.num_items = 1
                        note = " · 📧 Notification sent!" if email_sent else ""
                        st.success(f"✅ Order #{sr_no} saved with {len(items_data)} item(s)!{note}")
                    except Exception as e:
                        st.error(f"❌ Failed to save: {e}")


# ════════════════════════════════════════════════════════════════
# TAB 2 — View Orders
# ════════════════════════════════════════════════════════════════
with tab_view:
    if not secrets_configured():
        show_setup_warning()
    else:
        if st.button("🔄 Refresh"):
            load_orders.clear()
            st.rerun()

        with st.spinner("Loading orders…"):
            try:
                rows = load_orders()

                if not rows:
                    st.info("No orders yet. Add one in the 'New Order' tab.")
                else:
                    st.caption(f"{len(rows)} order(s) · tap Refresh for latest")

                    for row in rows:
                        # Pad row to 8 columns safely
                        while len(row) < 8:
                            row.append("")

                        sr       = row[0]
                        ts       = row[1]
                        del_date = row[2]
                        products = [p.strip() for p in row[3].split("|") if p.strip()]
                        packets  = [p.strip() for p in row[4].split("|")]
                        kgs      = [p.strip() for p in row[5].split("|")]
                        prices   = [p.strip() for p in row[6].split("|")]
                        notes_v  = row[7].strip()

                        # Build item rows HTML
                        items_html = ""
                        for idx, prod in enumerate(products):
                            pkt = packets[idx] if idx < len(packets) else "—"
                            kg  = kgs[idx]     if idx < len(kgs)     else "—"
                            pr  = prices[idx]  if idx < len(prices)  else "—"
                            # Show dashes for zero values
                            pkt_str = f"{pkt} Pkts" if pkt not in ("0","") else "—"
                            kg_str  = f"{kg} KG"    if kg  not in ("0","0.0","") else "—"
                            pr_str  = f"₹{pr}"      if pr  not in ("0","0.0","") else "—"
                            items_html += f"""
                            <div style="background:#f8faff;border-left:3px solid #1a56db;
                                        border-radius:8px;padding:8px 12px;margin-bottom:6px;">
                              <div style="font-weight:700;font-size:0.95rem;color:#111827;">{prod}</div>
                              <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px;">
                                <span style="background:#eff6ff;color:#1d4ed8;font-size:0.78rem;
                                             font-weight:700;padding:2px 9px;border-radius:20px;">
                                  📦 {pkt_str}</span>
                                <span style="background:#f0fdf4;color:#15803d;font-size:0.78rem;
                                             font-weight:700;padding:2px 9px;border-radius:20px;">
                                  ⚖️ {kg_str}</span>
                                <span style="background:#fff7ed;color:#c2410c;font-size:0.78rem;
                                             font-weight:700;padding:2px 9px;border-radius:20px;">
                                  {pr_str}</span>
                              </div>
                            </div>"""

                        notes_html = (
                            f'<div style="font-size:0.85rem;color:#6b7280;font-style:italic;'
                            f'margin-top:6px;">💬 {notes_v}</div>'
                            if notes_v else ""
                        )

                        st.markdown(f"""
                        <div style="background:white;border:1.5px solid #e5e7eb;border-radius:14px;
                                    padding:14px 16px;margin-bottom:14px;
                                    box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                          <div style="font-size:1rem;font-weight:800;color:#1a56db;margin-bottom:4px;">
                            Order #{sr}</div>
                          <div style="font-size:0.78rem;color:#6b7280;margin-bottom:10px;">
                            🚚 Deliver by <b>{del_date}</b> &nbsp;·&nbsp; 🕐 {ts}</div>
                          {items_html}
                          {notes_html}
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Could not load orders: {e}")
