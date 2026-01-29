import streamlit as st
import pandas as pd
import os
from datetime import date, datetime
import io

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

# --- SESSION STATE BAŞLANGIÇ DEĞERLERİ ---
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
    """Veriyi dosyaya yazar."""
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
        detay_listesi.append(f"• {row['Ayrıntı']} ({row['Haber_Kaynagi']})")
    detaylar_str = "\n".join(detay_listesi)
    return toplam, kaynak_metni, detaylar_str

# --- CALLBACK FONKSİYONU (HATA ÇÖZÜMÜ BURADA) ---
def kaydet_ve_sifirla():
    """Butona basılınca çalışır: Kaydeder ve kutuları temizler."""
    # Session state'den değerleri al
    secilen_mudurlukler = st.session_state.form_mudurlukler
    
    if not secilen_mudurlukler:
        st.error("Lütfen en az bir müdürlük seçiniz!")
    else:
        # Kaydetme işlemi
        veri_kaydet_dosyaya(
            st.session_state.form_tarih,
            st.session_state.form_mudurlukler,
            st.session_state.form_kaynak,
            st.session_state.form_sayi,
            st.session_state.form_ayrinti
        )
        st.toast(f"✅ Kayıt Başarılı! ({len(secilen_mudurlukler)} Müdürlük Eklendi)")
        
        # SIFIRLAMA İŞLEMİ (Burada hata vermez)
        st.session_state.form_sayi = 1
        st.session_state.form_ayrinti = ""

# --- ARAYÜZ ---
st.set_page_config(page_title="Beykoz Raporlama", layout="wide")
st.title("📊 Beykoz Haber Hesapları - Yönetici Paneli")

# --- SOL MENÜ: VERİ GİRİŞİ ---
with st.sidebar:
    st.header("📝 Veri Girişi")
    
    with st.form("giris_formu", clear_on_submit=False):
        # Her inputa bir KEY atadık ki callback içinden erişebilelim
        st.date_input("Tarih", value=date.today(), key="form_tarih")
        st.multiselect("Müdürlükler", MUDURLUKLER, key="form_mudurlukler")
        st.selectbox("Kaynak", HABER_KAYNAKLARI, key="form_kaynak")
        st.number_input("Sayı", min_value=1, step=1, key="form_sayi")
        st.text_area("Ayrıntı", height=150, placeholder="Şikayet detayları...", key="form_ayrinti")
        
        # on_click PARAMETRESİ İLE FONKSİYONU BAĞLADIK
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

        st.markdown("---")
        st.markdown("### 🖨️ Rapor Çıktısı Al")
        
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
            col_ex, col_html = st.columns(2)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_ozet.to_excel(writer, sheet_name='Rapor', index=False)
                workbook = writer.book
                worksheet = writer.sheets['Rapor']
                wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
                worksheet.set_column('A:A', 20, wrap_format)
                worksheet.set_column('B:B', 25, wrap_format)
                worksheet.set_column('C:C', 15, wrap_format)
                worksheet.set_column('D:D', 30, wrap_format)
                worksheet.set_column('E:E', 60, wrap_format)
            
            col_ex.download_button("📄 Excel İndir", buffer.getvalue(), f"Rapor_{bas}_{bit}.xlsx", "application/vnd.ms-excel")

            df_ozet_html = df_ozet.copy()
            if "Detaylar" in df_ozet_html.columns:
                df_ozet_html["Detaylar"] = df_ozet_html["Detaylar"].str.replace("\n", "<br>")

            html_template = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: sans-serif; padding: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    th {{ background: #2980b9; color: white; padding: 10px; text-align: left; }}
                    td {{ border: 1px solid #ddd; padding: 10px; vertical-align: top; }}
                    tr:nth-child(even) {{ background: #f9f9f9; }}
                </style>
            </head>
            <body>
                <h2>📊 Beykoz Haber Raporu ({tarih_formatla(bas)} - {tarih_formatla(bit)})</h2>
                {df_ozet_html.to_html(index=False, escape=False)} 
            </body>
            </html>
            """
            col_html.download_button("🌐 HTML İndir", html_template, f"Rapor_{bas}_{bit}.html", "text/html")

    else:
        st.warning("Kayıt bulunamadı.")
else:
    st.info("Veri tabanı boş.")