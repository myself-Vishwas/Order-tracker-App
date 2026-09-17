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
  .product-block {
    background: #f8faff;
    border: 1.5px solid #c7d7f7;
    border-radius: 12px;
    padding: 12px 14px 8px;
    margin-bottom: 10px;
    position: relative;
  }
  .product-block-title {
    font-size: 0.8rem; font-weight: 700;
    color: #1a56db; margin-bottom: 8px;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .unit-label {
    display: inline-block;
    background: #e0e7ff; color: #3730a3;
    font-size: 0.72rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px;
    margin-bottom: 4px;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .unit-label-green {
    display: inline-block;
    background: #f0fdf4; color: #15803d;
    font-size: 0.72rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px;
    margin-bottom: 4px;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .unit-label-orange {
    display: inline-block;
    background: #fff7ed; color: #c2410c;
    font-size: 0.72rem; font-weight: 700;
    padding: 2px 8px; border-radius: 20px;
    margin-bottom: 4px;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  input, textarea, select,
  .stTextInput input, .stNumberInput input,
  .stTextArea textarea, .stDateInput input,
  .stSelectbox div[data-baseweb="select"] {
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
  .stButton > button:hover  { background: #1648c0 !important; }
  .stButton > button:active { background: #1240b0 !important; }
  .add-btn > button {
    background: #f0fdf4 !important;
    color: #15803d !important;
    border: 1.5px solid #86efac !important;
    font-size: 0.9rem !important;
    padding: 8px !important;
    margin-top: 4px;
  }
  .remove-btn > button {
    background: #fff1f2 !important;
    color: #be123c !important;
    border: 1.5px solid #fda4af !important;
    font-size: 0.85rem !important;
    padding: 6px 10px !important;
    margin-top: 0 !important;
    width: auto !important;
  }
  .stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: #f3f4f6;
    border-radius: 12px; padding: 4px; margin-bottom: 16px;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 9px; font-weight: 600;
    font-size: 0.9rem; padding: 8px 0;
  }
  .success-banner {
    background: #ecfdf5; border: 1.5px solid #6ee7b7;
    color: #065f46; border-radius: 12px;
    padding: 14px 16px; font-weight: 600;
    font-size: 0.95rem; margin-top: 10px;
  }
  .setup-warning {
    background: #fef3c7; border: 1.5px solid #f59e0b;
    border-radius: 12px; padding: 16px;
    color: #92400e; font-size: 0.93rem; line-height: 1.6;
  }
  .order-card {
    background: white; border: 1.5px solid #e5e7eb;
    border-radius: 14px; padding: 14px 16px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }
  .order-meta { font-size: 0.78rem; color: #6b7280; margin-bottom: 6px; }
  .order-id   { font-size: 1rem; font-weight: 800; color: #1a56db; margin-bottom: 8px; }
  .item-row {
    background: #f8faff; border-radius: 10px;
    padding: 8px 12px; margin-bottom: 6px;
    border-left: 3px solid #1a56db;
  }
  .item-name  { font-weight: 700; font-size: 0.95rem; color: #111827; }
  .item-meta  { font-size: 0.8rem; color: #4b5563; margin-top: 2px; }
  .badges     { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
  .badge-blue  { background:#eff6ff; color:#1d4ed8; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:20px; }
  .badge-green { background:#f0fdf4; color:#15803d; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:20px; }
  .badge-orange{ background:#fff7ed; color:#c2410c; font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:20px; }
  .notes-text { font-size:0.85rem; color:#6b7280; font-style:italic; margin-top:6px; }
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
      Google Sheets credentials haven't been added to Streamlit.<br><br>
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
    items = list of dicts: {product, packets, kg, price}
    Saved as ONE row per order.
    Columns: Sr.No | Timestamp | Delivery Date | Products Summary |
             Packets Summary | KG Summary | Price Summary | Notes
    """
    sheet = get_sheet()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_rows  = sheet.get_all_values()
    data_rows = [r for r in all_rows[2:] if any(c.strip() for c in r)]
    next_sr   = len(data_rows) + 1

    # Build summary strings (pipe-separated per item)
    products = " | ".join(i["product"]          for i in items)
    packets  = " | ".join(str(i["packets"])     for i in items)
    kgs      = " | ".join(str(i["kg"])          for i in items)
    prices   = " | ".join(str(i["price"])       for i in items)

    sheet.append_row(
        [next_sr, timestamp, delivery_date, products, packets, kgs, prices, notes],
        value_input_option="USER_ENTERED",
    )
    return next_sr, timestamp


@st.cache_data(ttl=30, show_spinner=False)
def load_orders():
    sheet = get_sheet()
    all_values = sheet.get_all_values()
    if len(all_values) < 3:
        return pd.DataFrame(columns=["Sr. No","Timestamp","Delivery Date",
                                     "Products","No. of Packets","KG","Price Rate","Notes"])
    headers = all_values[1]
    data = [r for r in all_values[2:] if any(c.strip() for c in r)]
    if not data:
        return pd.DataFrame(columns=headers)
    df = pd.DataFrame(data, columns=headers)
    return df.iloc[::-1].reset_index(drop=True)


# ── Email ─────────────────────────────────────────────────────────────────────
def send_order_email(sr_no, timestamp, delivery_date, items, notes):
    try:
        sender    = st.secrets["EMAIL_SENDER"]
        password  = st.secrets["EMAIL_PASSWORD"]
        recipient = st.secrets["EMAIL_RECIPIENT"]
    except Exception:
        return False

    lines = "\n".join(
        f"  {idx+1}. {i['product']} — {i['packets']} pkts | {i['kg']} KG | ₹{i['price']}"
        for idx, i in enumerate(items)
    )
    subject = f"🍪 New Order #{sr_no} ({len(items)} item{'s' if len(items)>1 else ''})"
    body = f"""
🍪 New Order Received — Mali's Cookies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Order No   : #{sr_no}
🕐 Logged At  : {timestamp}
🚚 Deliver By : {delivery_date}

🛒 Items Ordered:
{lines}

📝 Notes : {notes if notes else "—"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
View all → https://order-tracker-app-vx2f29k26i86h9nrwyaatt.streamlit.app/
    """.strip()

    try:
        msg = MIMEMultipart()
        msg["From"] = sender; msg["To"] = recipient; msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())
        return True
    except Exception:
        return False


# ── Session state — product lines ─────────────────────────────────────────────
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


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_enter, tab_view = st.tabs(["➕  New Order", "📋  View Orders"])


# ── TAB 1 — New Order ─────────────────────────────────────────────────────────
with tab_enter:
    if not secrets_configured():
        show_setup_warning()
    else:
        # ── Delivery date & notes OUTSIDE form so Add/Remove buttons work ──
        st.markdown('<p class="field-label">Delivery Date</p>', unsafe_allow_html=True)
        delivery_date = st.date_input(
            "delivery_date", value=date.today(),
            min_value=date.today(), label_visibility="collapsed"
        )

        st.markdown('<p class="field-label">Products Ordered</p>', unsafe_allow_html=True)

        # ── Dynamic product lines ──────────────────────────────────────────
        items_data = []
        for i in range(st.session_state.num_items):
            st.markdown(
                f'<div class="product-block-title">🛒 Item {i+1}</div>',
                unsafe_allow_html=True
            )
            with st.container():
                st.markdown('<p class="field-label">Product</p>', unsafe_allow_html=True)
                prod = st.selectbox(
                    f"product_{i}", PRODUCTS,
                    key=f"prod_{i}", label_visibility="collapsed"
                )

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown('<span class="unit-label">📦 Packets</span>', unsafe_allow_html=True)
                    pkts = st.number_input(
                        f"pkts_{i}", min_value=0, step=1, value=0,
                        key=f"pkts_{i}", label_visibility="collapsed"
                    )
                with c2:
                    st.markdown('<span class="unit-label-green">⚖️ KG</span>', unsafe_allow_html=True)
                    kg = st.number_input(
                        f"kg_{i}", min_value=0.0, step=0.5,
                        value=0.0, format="%.1f",
                        key=f"kg_{i}", label_visibility="collapsed"
                    )
                with c3:
                    st.markdown('<span class="unit-label-orange">₹ Price</span>', unsafe_allow_html=True)
                    price = st.number_input(
                        f"price_{i}", min_value=0.0, step=1.0,
                        value=0.0, format="%.0f",
                        key=f"price_{i}", label_visibility="collapsed"
                    )

                items_data.append({
                    "product": prod,
                    "packets": int(pkts),
                    "kg": float(kg),
                    "price": float(price),
                })

                # Remove button (only show if more than 1 item)
                if st.session_state.num_items > 1:
                    st.markdown('<div class="remove-btn">', unsafe_allow_html=True)
                    if st.button(f"✕ Remove Item {i+1}", key=f"remove_{i}"):
                        st.session_state.num_items -= 1
                        # Clear keys for removed item
                        for k in [f"prod_{i}", f"pkts_{i}", f"kg_{i}", f"price_{i}"]:
                            st.session_state.pop(k, None)
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")

        # ── Add product button ─────────────────────────────────────────────
        st.markdown('<div class="add-btn">', unsafe_allow_html=True)
        if st.button("＋ Add Another Product"):
            st.session_state.num_items += 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<p class="field-label">Notes</p>', unsafe_allow_html=True)
        notes = st.text_area(
            "notes", placeholder="Special instructions, packaging, urgency…",
            label_visibility="collapsed"
        )

        # ── Save button ────────────────────────────────────────────────────
        if st.button("💾 Save Order →"):
            # Validate — at least one item needs packets or kg
            invalid = [
                i+1 for i, it in enumerate(items_data)
                if it["packets"] == 0 and it["kg"] == 0.0
            ]
            if invalid:
                st.error(f"⚠️ Item(s) {invalid}: please enter Packets or KG.")
            else:
                with st.spinner("Saving order…"):
                    try:
                        sr_no, timestamp = append_order(
                            str(delivery_date), items_data, notes.strip()
                        )
                        load_orders.clear()
                        email_sent = send_order_email(
                            sr_no, timestamp, str(delivery_date),
                            items_data, notes.strip()
                        )
                        # Reset to 1 item after successful save
                        for k in list(st.session_state.keys()):
                            if any(k.startswith(p) for p in ["prod_","pkts_","kg_","price_"]):
                                del st.session_state[k]
                        st.session_state.num_items = 1

                        email_note = " · 📧 Notification sent!" if email_sent else ""
                        st.success(f"✅ Order #{sr_no} saved with {len(items_data)} item(s)!{email_note}")
                    except Exception as e:
                        st.error(f"❌ Failed to save: {e}")


# ── TAB 2 — View Orders ───────────────────────────────────────────────────────
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

                    # Detect correct column names flexibly
                    col_prod  = next((c for c in df.columns if "Product" in c), None)
                    col_pkts  = next((c for c in df.columns if "Packet" in c), None)
                    col_kg    = next((c for c in df.columns if "KG" in c or "Kg" in c), None)
                    col_price = next((c for c in df.columns if "Price" in c), None)
                    col_notes = next((c for c in df.columns if "Note" in c), None)

                    for _, row in df.iterrows():
                        # Parse pipe-separated items
                        products = str(row.get(col_prod, "")).split(" | ")
                        packets  = str(row.get(col_pkts, "")).split(" | ")
                        kgs      = str(row.get(col_kg,   "")).split(" | ")
                        prices   = str(row.get(col_price,"")).split(" | ")

                        items_html = ""
                        for idx, prod in enumerate(products):
                            pkt = packets[idx] if idx < len(packets) else "—"
                            kg  = kgs[idx]     if idx < len(kgs)     else "—"
                            pr  = prices[idx]  if idx < len(prices)  else "—"
                            items_html += f"""
                            <div class="item-row">
                              <div class="item-name">{prod.strip()}</div>
                              <div class="badges">
                                <span class="badge-blue">📦 {pkt} Pkts</span>
                                <span class="badge-green">⚖️ {kg} KG</span>
                                <span class="badge-orange">₹ {pr}</span>
                              </div>
                            </div>"""

                        notes_val = str(row.get(col_notes,"")).strip()
                        notes_html = f'<div class="notes-text">💬 {notes_val}</div>' if notes_val else ""

                        sr  = row.get("Sr. No", "")
                        dt  = row.get("Delivery Date", "")
                        ts  = row.get("Timestamp", "")

                        st.markdown(f"""
                        <div class="order-card">
                          <div class="order-id">Order #{sr}</div>
                          <div class="order-meta">🚚 Deliver by {dt} &nbsp;·&nbsp; 🕐 {ts}</div>
                          {items_html}
                          {notes_html}
                        </div>
                        """, unsafe_allow_html=True)

                    with st.expander("Show full data table"):
                        st.dataframe(df, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"❌ Could not load orders: {e}")
                st.info("Check your secrets are correctly configured.")
