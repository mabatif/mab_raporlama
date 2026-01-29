
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import io
from fpdf import FPDF

# --- SAYFA AYARLARI (EN BAŞTA OLMALI) ---
st.set_page_config(
    page_title="Beykoz Rapor",  # Sekmede görünecek isim
    page_icon="📊",             # Sekmede görünecek ikon
    layout="wide"
)

# --- AYARLAR ---
DOSYA_ADI = 'beykoz_veritabani_v2.csv'

MUDURLUKLER = [
    "Fen İşleri Müdürlüğü", "Temizlik İşleri Müdürlüğü", "Zabıta Müdürlüğü", 
    "Spor Müdürlüğü", "Veteriner İşleri Müdürlüğü", "Park ve Bahçeler Müdürlüğü", 
    "Kültür Müdürlüğü", "Özel Kalem Müdürlüğü", "İşletme ve İştirakler Müdürlüğü", 
    "Emlak ve İstimlak Müdürlüğü", "İmar ve Şehircilik Müdürlüğü", "Diğer"
]
HABER_KAYNAKLARI = [
    "Beykoz Anlık", "Beykoz Burada", "Beykoz Duysun", "Beykoz Güncel", "Diğer"
]

# --- SESSION STATE ---
if 'form_sayi' not in st.session_state:
    st.session_state['form_sayi'] = 1
if 'form_ayrinti' not in st.session_state:
    st.session_state['form_ayrinti'] = ""

# --- YARDIMCI FONKSİYONLAR ---
def tarih_formatla(tarih_obj):
    if isinstance(tarih_obj, str):
        try:
            tarih_obj = datetime.strptime(tarih_obj, '%Y-%m-%d').date()
        except:
            return tarih_obj
    gunler = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
    return f"{tarih_obj.strftime('%d.%m.%Y')} {gunler[tarih_obj.weekday()]}"

def veri_yukle():
    if not os.path.exists(DOSYA_ADI):
        df = pd.DataFrame(columns=["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"])
        df.to_csv(DOSYA_ADI, index=False)
        return df
    return pd.read_csv(DOSYA_ADI).fillna("")

def veri_kaydet_dosyaya(tarih, mudurluk_listesi, kaynak, sayi, ayrinti):
    yeni_veriler = []
    for mud in mudurluk_listesi:
        yeni_veriler.append({
            "Tarih": tarih, 
            "Müdürlük": mud, 
            "Haber_Kaynagi": kaynak,
            "Sayı": sayi, 
            "Ayrıntı": ayrinti, 
            "Kayit_Zamani": datetime.now()
        })
    df_yeni = pd.DataFrame(yeni_veriler)
    df_yeni.to_csv(DOSYA_ADI, mode='a', header=not os.path.exists(DOSYA_ADI), index=False)

def ozet_metni_olustur(grup):
    toplam = grup['Sayı'].sum()
    kaynak_dagilimi = grup.groupby('Haber_Kaynagi')['Sayı'].sum()
    kaynak_metni = ", ".join([f"{k}: {v}" for k, v in kaynak_dagilimi.items()])
    detay_listesi = []
    for index, row in grup.iterrows():
        detay_listesi.append(f"- {row['Ayrıntı']} ({row['Haber_Kaynagi']})")
    detaylar_str = "\n".join(detay_listesi)
    return toplam, kaynak_metni, detaylar_str

# --- GELİŞMİŞ PDF TASARIMI (TABLO GÖRÜNÜMÜ) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(150)
        self.cell(0, 5, 'Beykoz Haber Takip Sistemi', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150)
        self.cell(0, 10, f'Sayfa {self.page_no()}', 0, 0, 'C')

def tr_karakter_duzelt(text):
    if not isinstance(text, str): return str(text)
    ceviri = str.maketrans("ğĞıİşŞçÇöÖüÜ", "gGiIsScCoOuU")
    return text.translate(ceviri)

def create_pdf_report(dataframe, bas_t, bit_t):
    # Orientation 'L' = Landscape (Yatay)
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # 1. RAPOR BAŞLIĞI
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(44, 62, 80)
    baslik = tr_karakter_duzelt(f"BEYKOZ HABER RAPORU ({tarih_formatla(bas_t)} - {tarih_formatla(bit_t)})")
    pdf.cell(0, 10, baslik, ln=True, align='C')
    pdf.ln(5)

    # 2. TABLO BAŞLIKLARI
    w_tarih = 25
    w_mudurluk = 50
    w_kaynak = 35
    w_sayi = 15
    w_ayrinti = 150 

    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(50, 50, 100)

    header_h = 8
    pdf.cell(w_tarih, header_h, "Tarih", 1, 0, 'C', fill=True)
    pdf.cell(w_mudurluk, header_h, "Mudurluk", 1, 0, 'C', fill=True)
    pdf.cell(w_kaynak, header_h, "Kaynak", 1, 0, 'C', fill=True)
    pdf.cell(w_sayi, header_h, "Adet", 1, 0, 'C', fill=True)
    pdf.cell(w_ayrinti, header_h, "Ayrinti / Sikayet", 1, 1, 'C', fill=True)

    # 3. TABLO İÇERİĞİ
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(0, 0, 0)
    
    fill = False
    df_sorted = dataframe.sort_values(by=['Tarih', 'Müdürlük'])

    for i, row in df_sorted.iterrows():
        tarih = tr_karakter_duzelt(tarih_formatla(row['Tarih']))
        mudurluk = tr_karakter_duzelt(row['Müdürlük'])
        kaynak = tr_karakter_duzelt(row['Haber_Kaynagi'])
        sayi = str(row['Sayı'])
        ayrinti = tr_karakter_duzelt(row['Ayrıntı'])

        satir_sayisi = max(1, len(ayrinti) // 95 + 1) 
        h_satir = 6 * satir_sayisi

        if pdf.get_y() + h_satir > 190:
            pdf.add_page()
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(41, 128, 185)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(w_tarih, header_h, "Tarih", 1, 0, 'C', fill=True)
            pdf.cell(w_mudurluk, header_h, "Mudurluk", 1, 0, 'C', fill=True)
            pdf.cell(w_kaynak, header_h, "Kaynak", 1, 0, 'C', fill=True)
            pdf.cell(w_sayi, header_h, "Adet", 1, 0, 'C', fill=True)
            pdf.cell(w_ayrinti, header_h, "Ayrinti / Sikayet", 1, 1, 'C', fill=True)
            pdf.set_font("Arial", size=9)
            pdf.set_text_color(0, 0, 0)

        if fill:
            pdf.set_fill_color(235, 245, 251)
        else:
            pdf.set_fill_color(255, 255, 255)

        x_baslangic = pdf.get_x()
        y_baslangic = pdf.get_y()

        pdf.cell(w_tarih, h_satir, tarih, 1, 0, 'C', fill=True)
        
        if len(mudurluk) > 25: 
             pdf.set_font("Arial", size=7)
             pdf.cell(w_mudurluk, h_satir, mudurluk, 1, 0, 'L', fill=True)
             pdf.set_font("Arial", size=9)
        else:
             pdf.cell(w_mudurluk, h_satir, mudurluk, 1, 0, 'L', fill=True)
             
        pdf.cell(w_kaynak, h_satir, kaynak, 1, 0, 'C', fill=True)
        pdf.cell(w_sayi, h_satir, sayi, 1, 0, 'C', fill=True)
        
        x_ayrinti = x_baslangic + w_tarih + w_mudurluk + w_kaynak + w_sayi
        pdf.set_xy(x_ayrinti, y_baslangic)
        pdf.multi_cell(w_ayrinti, 6, ayrinti, border=1, align='L', fill=True)
        pdf.set_xy(x_baslangic, y_baslangic + h_satir)

        fill = not fill

    return pdf.output(dest='S').encode('latin-1')

# --- CALLBACK FONKSİYONU ---
def kaydet_ve_sifirla():
    secilen_mudurlukler = st.session_state.form_mudurlukler
    if not secilen_mudurlukler:
        st.error("Lütfen en az bir müdürlük seçiniz!")
    else:
        veri_kaydet_dosyaya(
            st.session_state.form_tarih,
            st.session_state.form_mudurlukler,
            st.session_state.form_kaynak,
            st.session_state.form_sayi,
            st.session_state.form_ayrinti
        )
        st.toast(f"✅ Kayıt Başarılı! ({len(secilen_mudurlukler)} Müdürlük Eklendi)")
        st.session_state.form_sayi = 1
        st.session_state.form_ayrinti = ""

# --- ARAYÜZ ---
st.title("📊 Beykoz Haber Hesapları - Yönetici Paneli")

# --- SOL MENÜ: VERİ GİRİŞİ ---
with st.sidebar:
    st.header("📝 Veri Girişi")
    with st.form("giris_formu", clear_on_submit=False):
        st.date_input("Tarih", value=date.today(), key="form_tarih")
        st.multiselect("Müdürlükler", MUDURLUKLER, key="form_mudurlukler")
        st.selectbox("Kaynak", HABER_KAYNAKLARI, key="form_kaynak")
        st.number_input("Sayı", min_value=1, step=1, key="form_sayi")
        st.text_area("Ayrıntı", height=150, placeholder="Şikayet detayları...", key="form_ayrinti")
        st.form_submit_button("💾 Kaydet", on_click=kaydet_ve_sifirla)

# --- ANA EKRAN ---
df = veri_yukle()
if not df.empty:
    df['Tarih'] = pd.to_datetime(df['Tarih']).dt.date

# FİLTRELER
st.markdown("### 🔍 Rapor Filtreleme")
c1, c2, c3, c4 = st.columns(4)
bas = c1.date_input("Başlangıç", date.today())
bit = c2.date_input("Bitiş", date.today())
mud_sec = c3.multiselect("Müdürlük", MUDURLUKLER)
kaynak_sec = c4.multiselect("Kaynak", HABER_KAYNAKLARI)

if not df.empty:
    mask = (df['Tarih'] >= bas) & (df['Tarih'] <= bit)
    if mud_sec: mask &= df['Müdürlük'].isin(mud_sec)
    if kaynak_sec: mask &= df['Haber_Kaynagi'].isin(kaynak_sec)
    df_filt = df.loc[mask]

    if not df_filt.empty:
        # --- 1. LİSTELEME VE DÜZENLEME ---
        st.markdown("---")
        st.subheader("📋 Kayıtlar (Düzenle / Sil)")
        st.info("💡 Tabloyu açarak detayları görebilirsiniz.")

        grouped = df_filt.groupby(['Tarih', 'Müdürlük'])
        for (trh, mud), grup in grouped:
            trh_str = tarih_formatla(trh)
            toplam_sayi = grup['Sayı'].sum()
            
            with st.expander(f"📅 {trh_str}  |  🏢 {mud}  |  Toplam: {toplam_sayi}"):
                edited_grup = st.data_editor(
                    grup, num_rows="dynamic", key=f"editor_{trh}_{mud}", 
                    use_container_width=True, hide_index=True,
                    column_config={
                        "Kayit_Zamani": None, 
                        "Tarih": st.column_config.DateColumn("Tarih", format="DD.MM.YYYY"),
                        "Ayrıntı": st.column_config.TextColumn("Ayrıntı", width="large")
                    }
                )
                col_save, _ = st.columns([1, 4])
                if col_save.button("💾 Kaydet", key=f"btn_{trh}_{mud}"):
                    original_indexes = grup.index
                    df = df.drop(original_indexes)
                    if not edited_grup.empty:
                        edited_grup['Tarih'] = pd.to_datetime(edited_grup['Tarih']).dt.date
                        df = pd.concat([df, edited_grup], ignore_index=True)
                    df.to_csv(DOSYA_ADI, index=False)
                    st.success("Güncellendi!")
                    st.rerun()

        # --- 2. ÇIKTI ALMA (EXCEL, HTML ve PDF) ---
        st.markdown("---")
        st.subheader("🖨️ Rapor Çıktısı Al")
        
        tum_sutunlar = ["Tarih (Formatlı)", "Müdürlük", "Toplam Sayı", "Kaynak Dağılımı", "Detaylar"]
        secilen_sutunlar = st.multiselect("Sütun Seçimi", tum_sutunlar, default=tum_sutunlar)
        
        if secilen_sutunlar:
            ozet_liste = []
            for (trh, mud), grup in df_filt.groupby(['Tarih', 'Müdürlük']):
                toplam, kaynak_txt, detay_txt = ozet_metni_olustur(grup)
                ozet_liste.append({
                    "Tarih (Formatlı)": tarih_formatla(trh),
                    "Müdürlük": mud,
                    "Toplam Sayı": toplam,
                    "Kaynak Dağılımı": kaynak_txt,
                    "Detaylar": detay_txt
                })
            
            df_ozet = pd.DataFrame(ozet_liste)[secilen_sutunlar]
            col_ex, col_html, col_pdf = st.columns(3)

            # EXCEL
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_ozet.to_excel(writer, sheet_name='Rapor', index=False)
                workbook = writer.book
                worksheet = writer.sheets['Rapor']
                wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
                worksheet.set_column('A:E', 20, wrap_format)
            col_ex.download_button("📄 Excel İndir", buffer.getvalue(), f"Rapor_{bas}_{bit}.xlsx", "application/vnd.ms-excel")

            # HTML
            df_ozet_html = df_ozet.copy()
            if "Detaylar" in df_ozet_html.columns:
                df_ozet_html["Detaylar"] = df_ozet_html["Detaylar"].str.replace("\n", "<br>")
            html_template = f"<html><body><h2>Rapor ({tarih_formatla(bas)} - {tarih_formatla(bit)})</h2>{df_ozet_html.to_html(index=False, escape=False)}</body></html>"
            col_html.download_button("🌐 HTML İndir", html_template, f"Rapor_{bas}_{bit}.html", "text/html")

            # PDF (GELİŞMİŞ TABLO)
            pdf_data = create_pdf_report(df_filt, bas, bit)
            col_pdf.download_button("📕 PDF İndir (Tablo)", pdf_data, f"Rapor_{bas}_{bit}.pdf", "application/pdf")

        # --- 3. DASHBOARD BÖLÜMÜ ---
        st.markdown("---")
        st.subheader("📈 Veri Analizi ve Özet")
        
        m1, m2, m3 = st.columns(3)
        toplam_vaka = df_filt['Sayı'].sum()
        if not df_filt.empty:
            en_cok_haber = df_filt.groupby('Müdürlük')['Sayı'].sum().idxmax()
        else:
            en_cok_haber = "-"
        aktif_kaynak = df_filt['Haber_Kaynagi'].nunique()

        m1.metric("Toplam Haber/Şikayet", toplam_vaka)
        m2.metric("En Yoğun Müdürlük", en_cok_haber)
        m3.metric("Farklı Kaynak Sayısı", aktif_kaynak)

        st.markdown("<br>", unsafe_allow_html=True)
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.caption("🏢 Müdürlük Bazlı Dağılım")
            mud_data = df_filt.groupby('Müdürlük')['Sayı'].sum().sort_values(ascending=True)
            st.bar_chart(mud_data, horizontal=True, color="#2980b9")

        with col_chart2:
            st.caption("📅 Günlük Haber Akışı")
            zaman_data = df_filt.groupby('Tarih')['Sayı'].sum()
            st.line_chart(zaman_data, color="#27ae60")

    else:
        st.warning("Bu filtreleme kriterlerine uygun kayıt bulunamadı.")
else:
    st.info("Veri tabanı boş. Sol menüden ilk kaydı ekleyebilirsiniz.")
