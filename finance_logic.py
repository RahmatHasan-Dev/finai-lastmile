import google.generativeai as genai
from datetime import datetime
import json

API_KEY = "PASTE_API_KEY_DISINI"
genai.configure(api_key=API_KEY)

MODEL_NAME = 'gemini-1.5-flash'

def safe_generate_content(prompt):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        return model.generate_content(prompt)
    except Exception as e:
        if "404" in str(e):
            fallback_model = genai.GenerativeModel('gemini-pro')
            return fallback_model.generate_content(prompt)
        raise e

def get_ai_advice(user_data, user_query):
    try:
        last_exp = user_data.get('expenses', [])[-5:] if user_data.get('expenses') else []
        balance = user_data.get('balance', 0)
        
        expenses_summary = ""
        if last_exp:
            for exp in last_exp:
                expenses_summary += f"- {exp.get('item', 'N/A')}: Rp {exp.get('amount', 0):,} ({exp.get('category', 'Lainnya')})\n"
        
        context = f"""
Anda adalah asisten keuangan pribadi profesional AI.
Data Kondisi Keuangan Saat Ini:
- Sisa Saldo: Rp {balance:,}
- 5 Transaksi Terakhir:
{expenses_summary if expenses_summary else "Belum ada transaksi tercatat."}

Pertanyaan User: {user_query}

Instruksi:
1. Berikan saran keuangan yang praktis, singkat, dan mudah dipahami
2. Gunakan bahasa Indonesia yang ramah dan profesional
3. Jika memungkinkan, berikan contoh konkret atau angka
4. Berikan tips yang dapat langsung ditindaklanjuti
5. JANGAN gunakan emoji dalam jawaban Anda
6. Jika pertanyaan tentang investasi, jelaskan risiko juga

Jawaban:
"""
        
        response = safe_generate_content(context)
        return response.text
        
    except Exception as e:
        return f"Maaf, ada masalah dengan layanan AI. Error: {str(e)}. Silakan coba lagi dalam beberapa saat."


def get_ai_budget_advice(user_data, category=None):
    try:
        balance = user_data.get('balance', 0)
        income = user_data.get('income', [])
        expenses = user_data.get('expenses', [])
        
        total_income = sum(i.get('amount', 0) for i in income)
        
        from data_manager import get_expenses_by_category
        expenses_by_cat = get_expenses_by_category(user_data)
        
        cat_summary = "\n".join([f"- {cat}: Rp {amt:,}" for cat, amt in expenses_by_cat.items()])
        
        context = f"""
Anda adalah konsultan keuangan profesional.
Data keuangan user:
- Total Saldo: Rp {balance:,}
- Total Pemasukan Bulan Ini: Rp {total_income:,}
- Pengeluaran per Kategori:
{cat_summary if cat_summary else "Belum ada pengeluaran tercatat."}

{f'- Kategori yang ditanyakan: {category}' if category else ''}

Tugas:
1. Analisis pola pengeluaran user
2. Berikan rekomendasi alokasi budget untuk setiap kategori
3. Berikan tips mengoptimalkan pengeluaran
4. Gunakan metode 50/30/20 (50% kebutuhan, 30% keinginan, 20% tabungan) sebagai referensi
5. JANGAN gunakan emoji dalam jawaban Anda

Jawaban dalam bahasa Indonesia yang mudah dipahami:
"""
        
        response = safe_generate_content(context)
        return response.text
        
    except Exception as e:
        return f"Maaf, ada masalah dengan layanan AI. Error: {str(e)}"


def get_ai_expense_analysis(user_data):
    try:
        from data_manager import get_expenses_by_category, get_monthly_summary
        expenses_by_cat = get_expenses_by_category(user_data)
        monthly = get_monthly_summary(user_data)
        
        cat_summary = "\n".join([
            f"- {cat}: Rp {amt:,}" 
            for cat, amt in sorted(expenses_by_cat.items(), key=lambda x: x[1], reverse=True)
        ])
        
        context = f"""
Anda adalah analis keuangan profesional.
Analisis Pengeluaran Bulan Ini:
Total Pengeluaran: Rp {monthly['total_expenses']:,}
Total Pemasukan: Rp {monthly['total_income']:,}
Net Savings: Rp {monthly['net_savings']:,}

Pengeluaran per Kategori (dari tertinggi):
{cat_summary if cat_summary else "Belum ada pengeluaran tercatat."}

Tugas:
1. Identifikasi kategori dengan pengeluaran tertinggi
2. Berikan insights tentang pola pengeluaran
3. Berikan rekomendasi untuk menghemat keuangan
4. Berikan edukasi kepada pengguna cara mengalokasikan keuangan dengan lebih baik
5. Berikan tips spesifik berdasarkan data
6. JANGAN gunakan emoji dalam jawaban Anda

Jawaban dalam bahasa Indonesia yang menarik dan membantu:
"""
        
        response = safe_generate_content(context)
        return response.text
        
    except Exception as e:
        return f"Maaf, ada masalah dengan layanan AI. Error: {str(e)}"


def get_ai_savings_advice(user_data):
    try:
        from data_manager import get_monthly_summary
        monthly = get_monthly_summary(user_data)
        balance = user_data.get('balance', 0)
        goals = user_data.get('goals', [])
        total_income = monthly['total_income']
        
        goals_summary = ""
        for goal in goals:
            progress = (goal.get('current_amount', 0) / goal.get('target_amount', 1)) * 100
            goals_summary += f"- {goal.get('name')}: Rp {goal.get('current_amount', 0):,} / Rp {goal.get('target_amount', 0):,} ({progress:.1f}%)\n"
        
        context = f"""
Anda adalah penasihat keuangan specializes dalam perencanaan tabungan.
Data Tabungan User:
- Sisa Saldo: Rp {balance:,}
- Total Pemasukan: Rp {total_income:,}
- Goals Tabungan:
{goals_summary if goals_summary else "Belum ada goals tabungan."}

Tugas:
1. Analisis kemampuan user untuk menabung
2. Berikan strategi mencapai goals tabungan
3. Berikan rekomendasi alokasi untuk tabungan (minimal 20% dari income)
4. Berikan tips meningkatkan tabungan
5. Jika ada goals, berikan timeline realistis
6. JANGAN gunakan emoji dalam jawaban Anda

Jawaban dalam bahasa Indonesia yang motivating:
"""
        
        response = safe_generate_content(context)
        return response.text
        
    except Exception as e:
        return f"Maaf, ada masalah dengan layanan AI. Error: {str(e)}"


def get_ai_investment_advice(user_data, question=None):
    try:
        from data_manager import get_monthly_summary
        monthly = get_monthly_summary(user_data)
        balance = user_data.get('balance', 0)
        investments = user_data.get('investments', [])
        total_income = monthly['total_income']
        investment_summary = "\n".join([
            f"- {inv.get('name')}: Rp {inv.get('current_value', 0):,} ({inv.get('type')}) - Returns: Rp {inv.get('returns', 0):,}"
            for inv in investments
        ])
        
        context = f"""
Anda adalah penasihat investasi profesional dengan pengetahuan mendalam tentang pasar keuangan.
Data Investasi User:
- Sisa Saldo yang dapat diinvestasikan: Rp {balance:,}
- Total Pemasukan Bulanan: Rp {total_income:,}
- Portofolio Investasi Saat Ini:
{investment_summary if investment_summary else "Belum ada investasi."}

{f'Pertanyaan spesifik: {question}' if question else ''}

Peringatan Penting:
- Selalu jelaskan RISIKO dari setiap investasi
- Jangan pernah menjanjikan return pasti
- Sesuaikan rekomendasi dengan profil risiko user
- Gunakan prinsip diversifikasi

Tugas:
1. Berikan analisis portofolio saat ini
2. Berikan rekomendasi investasi sesuai kondisi keuangan
3. Jelaskan opsi investasi yang aman (deposito, reksadana, Obligasi, dll)
4. Berikan tips memulai investasi untuk pemula
5. Ingatkan pentingnya dana darurat (minimal 3-6 bulan pengeluaran) sebelum investasi
6. JANGAN gunakan emoji dalam jawaban Anda

Jawaban dalam bahasa Indonesia yang profesional dan bertanggung jawab:
"""
        
        response = safe_generate_content(context)
        return response.text
        
    except Exception as e:
        return f"Maaf, ada masalah dengan layanan AI. Error: {str(e)}"


def get_ai_full_report(user_data):
    try:
        from data_manager import generate_report
        report = generate_report(user_data)
        
        summary = report.get('summary', {})
        expenses_by_cat = report.get('expenses_by_category', {})
        goals = report.get('savings_goals', {})
        investments = report.get('investments', {})
        
        report_text = f"""
LAPORAN KEUANGAN
Tanggal: {report.get('generated_date')}

RINGKASAN:
- Total Saldo: Rp {summary.get('total_balance', 0):,}
- Total Pemasukan: Rp {summary.get('total_income', 0):,}
- Total Pengeluaran: Rp {summary.get('total_expenses', 0):,}
- Net Savings: Rp {summary.get('net_savings', 0):,}
- Total Transaksi: {summary.get('total_transactions', 0)}

PENGELUARAN PER KATEGORI:
"""
        for cat, amt in expenses_by_cat.items():
            report_text += f"- {cat}: Rp {amt:,}\n"
        
        report_text += f"""
TARGET TABUNGAN:
- Total Goals: {goals.get('total_goals', 0)}
- Aktif: {goals.get('active', 0)}
- Terealisasi: {goals.get('completed', 0)}

INVESTASI:
- Total Investasi: {investments.get('total_investments', 0)}
- Total Nilai: Rp {investments.get('total_value', 0):,}
- Total Returns: Rp {investments.get('total_returns', 0):,}
"""
        
        context = f"""
Berdasarkan data keuangan berikut, berikan analisis lengkap dan rekomendasi:

{report_text}

Tugas:
1. Berikan evaluasi kondisi keuangan secara keseluruhan
2. Identifikasi kekuatan dan kelemahan keuangan
3. Berikan rekomendasi perbaikan
4. Berikan tips untuk mencapai kebebasan keuangan
5. Buat ringkasan actionable yang dapat ditindaklanjuti
6. JANGAN gunakan emoji dalam jawaban Anda

Jawaban dalam bahasa Indonesia yang profesional namun mudah dipahami:
"""
        
        response = safe_generate_content(context)
        return response.text
        
    except Exception as e:
        return f"Maaf, ada masalah dengan layanan AI. Error: {str(e)}"


def chat_with_ai(user_data, message, chat_history=None):
    try:
        from data_manager import get_monthly_summary
        monthly = get_monthly_summary(user_data)
        balance = user_data.get('balance', 0)
        expenses = user_data.get('expenses', [])[-10:]  # 10 transaksi terakhir
        goals = user_data.get('goals', [])
        investments = user_data.get('investments', [])
        
        expenses_text = "\n".join([
            f"- {e.get('item')}: Rp {e.get('amount'):,} ({e.get('category')})"
            for e in expenses
        ]) if expenses else "Belum ada pengeluaran"
        
        income_total = monthly['total_income']
        
        goals_text = "\n".join([
            f"- {g.get('name')}: {g.get('current_amount')/g.get('target_amount')*100:.1f}% ({g.get('status')})"
            for g in goals
        ]) if goals else "Belum ada goals"
        
        investments_text = "\n".join([
            f"- {i.get('name')}: Rp {i.get('current_value'):,} ({i.get('type')})"
            for i in investments
        ]) if investments else "Belum ada investasi"
        
        history_context = ""
        if chat_history:
            for msg in chat_history[-6:]:
                role = "User" if msg['role'] == "user" else "AI"
                history_context += f"{role}: {msg['content']}\n"

        # Context building
        base_context = f"""
DATA KEUANGAN ANDA:
- Saldo: Rp {balance:,}
- Pemasukan Total: Rp {income_total:,}
- 10 Pengeluaran Terakhir:
{expenses_text}
- Goals Tabungan:
{goals_text}
- Investasi:
{investments_text}

PETUNJUK:
- Jawab dalam bahasa Indonesia yang natural dan friendly
- Gunakan format yang bersih dan JANGAN gunakan emoji
- Jangan terlalu panjang tapi juga jangan terlalu singkat
- Berikan jawaban yang actionable
- Jika user bertanya tentang topik spesifik, fokus pada topic tersebut

PERATURAN:
- Jangan pernah menyarankan investasi yang berisiko tinggi tanpa penjelasan risiko
- Selalu ingatkan untuk konsultasi dengan profesional untuk keputusan investasi besar

RIWAYAT PERCAKAPAN:
{history_context}

PESAN USER: {message}

Jawaban Anda:
"""
        
        response = safe_generate_content(base_context)
        return response.text
        
    except Exception as e:
        return f"Waduh, koneksi AI terputus (Error: {str(e)}). Pastikan Anda sudah menjalankan 'pip install -U google-generativeai' dan cek koneksi internet."
