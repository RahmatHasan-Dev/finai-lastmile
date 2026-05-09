import streamlit as st
import pandas as pd
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    st.error("Library 'plotly' tidak ditemukan. Silakan jalankan 'python -m pip install plotly' di terminal Anda.")
    st.stop()

from data_manager import (
    load_data, save_data, get_monthly_summary, get_historical_monthly_summaries, set_budget, 
    get_budget_status, add_savings_goal, update_savings_goal,
    add_investment, update_investment_value, generate_report, 
    delete_expense, delete_income, delete_goal, delete_investment,
    update_expense, update_income, calculate_health_score, get_investment_summary
)
from finance_logic import (
    get_ai_advice, get_ai_budget_advice, get_ai_expense_analysis,
    get_ai_savings_advice, get_ai_investment_advice, get_ai_full_report,
    chat_with_ai
)
from datetime import datetime

st.set_page_config(page_title="FinAI - Smart Personal Finance", layout="wide")
data = load_data()

st.markdown("""
    <style>
    /* Tema Putih Bersih & Profesional */
    .stApp { background-color: #FFFFFF; }
    
    /* Paksa Semua Teks Utama Menjadi Charcoal Dark agar Sangat Jelas */
    h1, h2, h3, h4, h5, h6, p, li, span, label { color: #1F2937 !important; }
    
    /* Kartu Metrik - Latar Abu-abu Sangat Muda agar Terpisah */
    [data-testid="stMetric"] { 
        background-color: #F9FAFB !important; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #E5E7EB !important;
    }
    [data-testid="stMetricValue"] { color: #1E3A8A !important; font-family: 'JetBrains Mono', monospace; }
    [data-testid="stMetricLabel"] { color: #4B5563 !important; font-weight: 600; }

    /* Tombol Utama - Navy Blue Solid agar Kontras Tajam */
    .stButton>button { border-radius: 6px; border: 1px solid #1E3A8A; background-color: #1E3A8A; color: #FFFFFF !important; font-weight: bold; }
    .stButton>button:hover { background-color: #111827; border-color: #111827; box-shadow: none; }

    /* Navigasi Tab */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #F3F4F6; color: #1F2937 !important; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: #FFFFFF !important; }

    /* Sidebar & Containers */
    [data-testid="stSidebar"] { background-color: #F9FAFB; border-right: 1px solid #E5E7EB; }
    div[data-testid="stExpander"], .stTable, .stDataFrame { background-color: #F9FAFB !important; border: 1px solid #E5E7EB !important; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("FinAI Assistant")
    st.divider()
    st.subheader("Transaksi Baru")
    tipe = st.selectbox("Tipe", ["Pengeluaran", "Pemasukan"])
    nama = st.text_input("Keterangan", placeholder="Misal: Gaji, Beli Kopi, dll")
    jumlah = st.number_input("Nominal (Rp)", min_value=0, step=1000)
    cat_options = ["Makan", "Transport", "Kebutuhan", "Hiburan", "Investasi", "Tagihan", "Lainnya"]
    kat = st.selectbox("Kategori", cat_options)
    tgl = st.date_input("Tanggal", datetime.now())
    
    if st.button("Simpan", type="primary"):
        if not nama.strip():
            st.error("Keterangan transaksi wajib diisi.")
        elif jumlah <= 0:
            st.error("Nominal harus lebih besar dari Rp 0.")
        else:
            entry = {"item": nama, "amount": jumlah, "category": kat, "date": tgl.strftime('%Y-%m-%d')}
            if tipe == "Pengeluaran":
                data.setdefault('expenses', []).append(entry)
                data['balance'] -= jumlah
            else:
                data.setdefault('income', []).append(entry)
                data['balance'] += jumlah
            save_data(data)
            st.success("Tersimpan!")
            st.rerun()

tabs = st.tabs([
    "Dashboard", "Anggaran", "Analisis", 
    "Asisten AI", "Target", "Investasi", "Laporan"
])

with tabs[0]:
    st.title("Financial Intelligence Terminal")
    m = get_monthly_summary(data)
    health_score = calculate_health_score(data)

    col_gauge, col_alerts = st.columns([0.5, 0.5])
    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode = "number+gauge",
            value = health_score,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "FINANCIAL HEALTH INDEX", 'font': {'size': 18, 'color': '#1E3A8A'}},
            number = {'font': {'color': '#1F2937', 'size': 44}, 'suffix': "%"},
            gauge = {
                'shape': "bullet",
                'axis': {'range': [0, 100], 'tickcolor': "#1F2937", 'tickfont': {'color': "#1F2937"}},
                'bar': {'color': "#1E3A8A"},
                'bgcolor': "#F3F4F6",
                'steps': [
                    {'range': [0, 50], 'color': '#FCA5A5'},
                    {'range': [50, 80], 'color': '#FDE68A'},
                    {'range': [80, 100], 'color': '#86EFAC'}
                ],
            }
        ))
        fig_gauge.update_layout(paper_bgcolor='#FFFFFF', font={'color': "#1F2937"}, height=160, margin=dict(l=40, r=40, t=60, b=40))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_alerts:
        status = get_budget_status(data)
        over_budget = [c for c, s in status.items() if s['percent_used'] > 100]
        if over_budget:
            st.error(f"Sistem Mendeteksi {len(over_budget)} Pelanggaran Anggaran")
            for cat in over_budget:
                st.write(f"- {cat}: Melebihi batas sebesar Rp {abs(status[cat]['remaining']):,}")
        else:
            st.success("Analisis Sistem: Parameter keuangan berada dalam zona hijau.")

    st.subheader("Metrik Utama Bulan Ini")
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("Saldo Saat Ini", f"Rp {data['balance']:,}")
    col_kpi2.metric("Pemasukan Bulan Ini", f"Rp {m['total_income']:,}")
    col_kpi3.metric("Pengeluaran Bulan Ini", f"Rp {m['total_expenses']:,}", delta=f"-{m['total_expenses']:,}", delta_color="inverse")
    col_kpi4.metric("Net Savings Bulan Ini", f"Rp {m['net_savings']:,}")

    st.divider()

    st.subheader("Gambaran Umum Keuangan")
    col_kpi_add1, col_kpi_add2, col_kpi_add3, col_kpi_add4 = st.columns(4)
    savings_rate = (m['net_savings'] / m['total_income'] * 100) if m['total_income'] > 0 else 0
    col_kpi_add1.metric("Savings Rate", f"{savings_rate:.1f}%")

    active_goals_count = len([g for g in data.get('goals', []) if g.get('status') == 'active'])
    col_kpi_add2.metric("Target Tabungan Aktif", f"{active_goals_count}")

    inv_summary = get_investment_summary(data)
    col_kpi_add3.metric("Total Investasi", f"{inv_summary['total_investments_count']}")
    col_kpi_add4.metric("ROI Investasi Keseluruhan", f"{inv_summary['overall_roi_percentage']:.2f}%")

    st.divider()

    st.subheader("Visualisasi Data Keuangan")
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.write("Pengeluaran per Kategori (Bulan Ini)")
        if m['expenses']:
            df_exp = pd.DataFrame(m['expenses'])
            fig_pie = px.pie(df_exp, values='amount', names='category', 
                             hole=0.4,
                             color_discrete_sequence=px.colors.sequential.ice)
            fig_pie.update_layout(
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FFFFFF',
                font_color="#1F2937",
                showlegend=True,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else: st.info("Belum ada data.")
    
    with col_chart2:
        historical_summaries = get_historical_monthly_summaries(data, num_months=6)
        if historical_summaries:
            df_history = pd.DataFrame(historical_summaries)
            fig_trend = px.line(df_history, x='month_year', y='net_savings', 
                                title="Pertumbuhan Kekayaan",
                                markers=True, color_discrete_sequence=['#00d4ff'])
            fig_trend.update_layout(
                paper_bgcolor='#FFFFFF',
                plot_bgcolor='#FFFFFF',
                font_color="#1F2937",
                xaxis_title="Periode",
                yaxis_title="Net Savings (Rp)"
            )
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("Belum ada data historis untuk tren.")

    st.divider()

    st.subheader("Aktivitas Terbaru")
    col_recent_exp, col_recent_inc = st.columns(2)
    with col_recent_exp:
        st.write("Pengeluaran Terakhir")
        if data.get('expenses'):
            df_exp_recent = pd.DataFrame(data['expenses']).sort_values(by='date', ascending=False).head(5)
            st.table(df_exp_recent.reindex(columns=['date', 'item', 'amount', 'category']))
        else: st.info("Belum ada pengeluaran.")
    with col_recent_inc:
        st.write("Pemasukan Terakhir")
        recent = (data.get('expenses', []) + data.get('income', []))[-5:]
        if recent:
            df_recent = pd.DataFrame(recent)
            st.table(df_recent.reindex(columns=['date', 'item', 'amount', 'category']))
        else: st.info("Kosong.")

# 2. BUDGET PLANNER
with tabs[1]:
    st.header("Perencanaan Anggaran")
    with st.expander("Set Budget Baru"):
        b_cat = st.selectbox("Kategori Budget", cat_options, key="b_cat")
        b_amt = st.number_input("Limit Budget (Rp)", min_value=0, step=50000)
        if st.button("Update Budget"):
            set_budget(data, b_cat, b_amt)
            st.success("Budget diperbarui!")
            st.rerun()

    status = get_budget_status(data)
    for cat, s in status.items():
        if s['budget'] > 0:
            st.write(f"**{cat}** (Rp {s['spent']:,} / Rp {s['budget']:,})")
            color = "red" if s['percent_used'] > 100 else "green"
            st.progress(min(s['percent_used']/100, 1.0))
            if s['remaining'] < 0: st.warning(f"Over budget: Rp {abs(s['remaining']):,}")

    if st.button("Dapatkan Strategi Budget AI"):
        with st.spinner("AI sedang menghitung..."):
            st.info(get_ai_budget_advice(data))

# 3. EXPENSE ANALYZER
with tabs[2]:
    st.header("Analisis Pengeluaran Mendalam")
    expenses_all = data.get('expenses', [])
    if expenses_all:
        df_all = pd.DataFrame(expenses_all)
        
        st.subheader("Filter Data")
        col_f1, col_f2 = st.columns(2)
        df_all['date'] = pd.to_datetime(df_all['date'])
        
        start_date = col_f1.date_input("Dari Tanggal", df_all['date'].min().date())
        end_date = col_f2.date_input("Sampai Tanggal", df_all['date'].max().date())
        
        mask = (df_all['date'].dt.date >= start_date) & (df_all['date'].dt.date <= end_date)
        df_filtered = df_all.loc[mask].sort_values(by='date', ascending=False)
        
        st.write("Daftar Transaksi")
        st.dataframe(df_filtered, use_container_width=True)
        
        if st.button("Minta Analisis AI"):
            st.write(get_ai_expense_analysis(data))
        
        st.divider()
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            with st.expander("Edit Transaksi"):
                idx_to_edit = st.number_input("Index Transaksi (Edit)", min_value=0, max_value=max(0, len(expenses_all)-1), step=1)
                if expenses_all:
                    target = expenses_all[idx_to_edit]
                    e_name = st.text_input("Keterangan", value=target['item'], key="edit_name")
                    e_amt = st.number_input("Nominal (Rp)", value=target['amount'], key="edit_amt")
                    e_cat = st.selectbox("Kategori", cat_options, index=cat_options.index(target['category']) if target['category'] in cat_options else 0, key="edit_cat")
                    e_tgl = st.date_input("Tanggal", datetime.strptime(target['date'], '%Y-%m-%d'), key="edit_date")
                    
                    if st.button("Simpan Perubahan"):
                        if not e_name.strip() or e_amt <= 0:
                            st.error("Data edit tidak valid. Periksa keterangan dan nominal.")
                        else:
                            updated = {"item": e_name, "amount": e_amt, "category": e_cat, "date": e_tgl.strftime('%Y-%m-%d')}
                            update_expense(data, idx_to_edit, updated)
                            st.success("Transaksi diperbarui")
                            st.rerun()

        with col_del:
            with st.expander("Hapus Transaksi"):
                idx_to_del = st.number_input("Index Transaksi (Hapus)", min_value=0, max_value=max(0, len(expenses_all)-1), step=1)
                if st.button("Hapus Secara Permanen"):
                    delete_expense(data, idx_to_del)
                    st.rerun()
    else: st.info("Data belum tersedia.")

# 4. AI FINANCIAL ADVISOR (CHAT)
with tabs[3]:
    st.header("Chat dengan FinAI Advisor")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Tanyakan sesuatu tentang keuanganmu..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                response = chat_with_ai(data, prompt, st.session_state.messages)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
    
    if st.button("Bersihkan Chat"):
        st.session_state.messages = []
        st.rerun()

# 5. SAVINGS GOALS
with tabs[4]:
    st.header("Target Tabungan")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("goal_form"):
            g_name = st.text_input("Nama Goal", placeholder="Misal: Liburan ke Jepang")
            g_target = st.number_input("Target (Rp)", min_value=0)
            g_date = st.date_input("Deadline")
            if st.form_submit_button("Tambah Goal"):
                add_savings_goal(data, g_name, g_target, g_date.strftime('%Y-%m-%d'))
                st.rerun()
    
    for g in data.get('goals', []):
        with st.container():
            st.subheader(g['name'])
            col_a, col_b = st.columns([0.7, 0.3])
            progress = (g['current_amount'] / g['target_amount']) if g['target_amount'] > 0 else 0
            col_a.progress(min(progress, 1.0))
            col_a.write(f"Progress: {progress*100:.1f}% (Rp {g['current_amount']:,} / Rp {g['target_amount']:,})")
            
            new_amt = col_b.number_input(f"Update Rp", key=f"up_{g['id']}", min_value=0)
            if col_b.button("Update", key=f"btn_{g['id']}"):
                update_savings_goal(data, g['id'], new_amt)
                st.rerun()
            if col_b.button("Hapus", key=f"del_{g['id']}"):
                delete_goal(data, g['id'])
                st.rerun()

    if st.button("Minta Strategi Menabung AI"):
        st.info(get_ai_savings_advice(data))

# 6. INVESTMENTS
with tabs[5]:
    st.header("Portofolio Investasi")
    with st.expander("Tambah Investasi"):
        i_name = st.text_input("Nama Instrumen", placeholder="Misal: Saham BBCA")
        i_amt = st.number_input("Modal Awal (Rp)", min_value=0)
        i_type = st.selectbox("Jenis", ["Saham", "Reksadana", "Emas", "Crypto", "Obligasi"])
        if st.button("Simpan Investasi"):
            add_investment(data, i_name, i_amt, i_type)
            st.rerun()

    if data.get('investments'):
        df_inv = pd.DataFrame(data['investments'])
        st.dataframe(df_inv, use_container_width=True)
        
        sel_inv = st.selectbox("Update Nilai Sekarang", [i['name'] for i in data['investments']])
        new_val = st.number_input("Nilai Baru (Rp)", min_value=0)
        if st.button("Update Nilai"):
            inv_id = next(i['id'] for i in data['investments'] if i['name'] == sel_inv)
            update_investment_value(data, inv_id, new_val)
            st.success("Nilai diperbarui!")
            st.rerun()
            
        if st.button("Dapatkan Analisis Investasi AI"):
            st.write(get_ai_investment_advice(data))
    else: st.info("Belum ada investasi.")

    st.divider()
    with st.expander("Simulasi Bunga Majemuk"):
        st.subheader("Proyeksi Investasi")
        c_sim1, c_sim2 = st.columns(2)
        principal = c_sim1.number_input("Modal Awal (Rp)", value=10000000, step=1000000)
        monthly_add = c_sim1.number_input("Kontribusi Bulanan (Rp)", value=1000000, step=100000)
        annual_rate = c_sim2.number_input("Suku Bunga Tahunan (%)", value=6.0, step=0.1)
        years = c_sim2.number_input("Durasi (Tahun)", value=5, min_value=1, max_value=50)
        
        if st.button("Hitung Simulasi"):
            r = annual_rate / 100 / 12
            n = int(years * 12)
            
            if r > 0:
                future_value = principal * (1 + r)**n + monthly_add * (((1 + r)**n - 1) / r)
            else:
                future_value = principal + (monthly_add * n)
                
            total_deposit = principal + (monthly_add * n)
            total_interest = future_value - total_deposit
            
            st.write(f"Estimasi Nilai Akhir: Rp {future_value:,.0f}")
            st.write(f"Total Modal Disetor: Rp {total_deposit:,.0f}")
            st.write(f"Total Keuntungan Bunga: Rp {total_interest:,.0f}")
            
            st.divider()
            col_viz1, col_viz2 = st.columns(2)
            
            with col_viz1:
                st.write("Proyeksi Pertumbuhan")
                growth_data = []
                periods = []
                for i in range(n + 1):
                    if r > 0:
                        val = principal * (1 + r)**i + (monthly_add * (((1 + r)**i - 1) / r) if i > 0 else 0)
                    else:
                        val = principal + (monthly_add * i)
                    growth_data.append(val)
                    periods.append(i)
                
                fig_growth = px.line(
                    x=periods, 
                    y=growth_data, 
                    labels={'x': 'Bulan', 'y': 'Saldo (Rp)'},
                    color_discrete_sequence=['#00d4ff']
                )
                fig_growth.update_layout(paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF', font_color="#1F2937", margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_growth, use_container_width=True)
                
            with col_viz2:
                st.write("Komposisi Modal vs Bunga")
                fig_sim = px.pie(
                    values=[total_deposit, max(0, total_interest)],
                    names=['Modal Disetor', 'Akumulasi Bunga'],
                    color_discrete_sequence=['#00d4ff', '#28a745'],
                    hole=0.3
                )
                fig_sim.update_layout(paper_bgcolor='#FFFFFF', font_color="#1F2937")
                st.plotly_chart(fig_sim, use_container_width=True)

# 7. REPORTS
with tabs[6]:
    st.header("Laporan Keuangan Lengkap")
    if st.button("Generate Laporan Full AI"):
        with st.spinner("Menyusun laporan..."):
            full_report = get_ai_full_report(data)
            st.markdown(full_report)
            
            st.download_button("Download Laporan", full_report, "laporan_keuangan.txt")
            
    st.divider()
    st.subheader("Data Master")
    c_exp, c_inc = st.columns(2)
    c_exp.write("Daftar Pengeluaran")
    c_exp.dataframe(pd.DataFrame(data.get('expenses', [])))
    
    c_inc.write("Daftar Pemasukan")
    income_list = data.get('income', [])
    c_inc.dataframe(pd.DataFrame(income_list))
    
    if income_list:
        with c_inc.expander("Kelola Pemasukan"):
            idx_inc = st.number_input("Index Pemasukan", min_value=0, max_value=max(0, len(income_list)-1), step=1)
            target_inc = income_list[idx_inc]
            
            i_name = st.text_input("Keterangan", value=target_inc['item'], key="inc_name")
            i_amt = st.number_input("Nominal (Rp)", value=target_inc['amount'], key="inc_amt")
            i_tgl = st.date_input("Tanggal", datetime.strptime(target_inc['date'], '%Y-%m-%d'), key="inc_date")
            
            col_inc_btn1, col_inc_btn2 = st.columns(2)
            if col_inc_btn1.button("Update Pemasukan"):
                updated_inc = {"item": i_name, "amount": i_amt, "category": target_inc.get('category', 'Lainnya'), "date": i_tgl.strftime('%Y-%m-%d')}
                update_income(data, idx_inc, updated_inc)
                st.rerun()
            
            if col_inc_btn2.button("Hapus Pemasukan"):
                delete_income(data, idx_inc)
                st.rerun()

    if st.button("RESET SEMUA DATA", type="secondary"):
        from data_manager import reset_data
        reset_data()
        st.rerun()