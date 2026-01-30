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

# V1.2 - GÜNCELLENMİŞ MÜDÜRLÜK LİSTESİ (ÖNCELİKLİ SIRALAMA)
MUDURLUKLER = [
    # ÖNCELİKLİ MÜDÜRLÜKLER (EN ÜSTTE)
    "Fen İşleri Müdürlüğü",
    "Temizlik İşleri Müdürlüğü", 
    "Zabıta Müdürlüğü",
    "İşletme ve İştirakler Müdürlüğü",
    "Özel Kalem Müdürlüğü",
    "Kültür ve Sosyal İşler Müdürlüğü",
    
    # DİĞER MÜDÜRLÜKLER (ALFABETİK)
    "Afet İşleri ve Risk Yönetimi Müdürlüğü",
    "Basın Yayın ve Halkla İlişkiler Müdürlüğü",
    "Bilgi İşlem Müdürlüğü",
    "Destek Hizmetleri Müdürlüğü",
    "Emlak ve İstimlak Müdürlüğü",
    "Gençlik ve Spor Hizmetleri Müdürlüğü",
    "Hukuk İşleri Müdürlüğü",
    "İklim Değişikliği ve Sıfır Atık Müdürlüğü",
    "İmar ve Şehircilik Müdürlüğü",
    "İnsan Kaynakları ve Eğitim Müdürlüğü",
    "Kentsel Dönüşüm Müdürlüğü",
    "Mali Hizmetler Müdürlüğü",
    "Muhtarlık İşleri Müdürlüğü",
    "Park ve Bahçeler Müdürlüğü",
    "Plan ve Proje Müdürlüğü",
    "Rehberlik ve Teftiş Kurulu Müdürlüğü",
    "Ruhsat ve Denetim Müdürlüğü",
    "Sağlık İşleri Müdürlüğü",
    "Sosyal Yardım İşleri Müdürlüğü",
    "Tarımsal Hizmetler Müdürlüğü",
    "Ulaşım Hizmetleri Müdürlüğü",
    "Veteriner İşleri Müdürlüğü",
    "Yapı Kontrol Müdürlüğü",
    "Yazı İşleri Müdürlüğü",
    
    # SON SEÇENEK
    "Diğer"
]

HABER_KAYNAKLARI = [
    "Beykoz Anlık", "Beykoz Burada", "Beykoz Duysun", "Beykoz Güncel", "Diğer"
]

# --- SESSION STATE ---
if 'form_sayi' not in st.session_state:
    st.session_state['form_sayi'] = 1
if 'form_ayrinti' not in st.session_state:
    st.session_state['form_ayrinti'] = ""
if 'pending_changes' not in st.session_state:
    st.session_state.pending_changes = False
# V1.3: Diğer kaynak için session state
if 'diger_kaynak' not in st.session_state:
    st.session_state.diger_kaynak = ""

# --- YARDIMCI FONKSİYONLAR ---
def tarih_formatla(tarih_obj):
    if isinstance(tarih_obj, str):
        try:
            # Gün/Ay/Yıl formatına dönüştür
            tarih_obj = datetime.strptime(tarih_obj, '%Y-%m-%d').date()
        except:
            try:
                tarih_obj = datetime.strptime(tarih_obj, '%d.%m.%Y').date()
            except:
                return str(tarih_obj)
    if hasattr(tarih_obj, 'strftime'):
        gunler = {0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe", 4: "Cuma", 5: "Cumartesi", 6: "Pazar"}
        return f"{tarih_obj.strftime('%d.%m.%Y')} {gunler[tarih_obj.weekday()]}"
    return str(tarih_obj)

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
    
    # V1.3 GÜNCELLEME: Sıralı numaralandırma (index değil, sıra numarası)
    for sira_no, (index, row) in enumerate(grup.iterrows(), 1):
        detay_listesi.append(f"{sira_no}. {row['Ayrıntı']} ({row['Haber_Kaynagi']})")
    
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
    if not isinstance(text, str): 
        return str(text)
    # Türkçe karakterleri İngilizce karşılıklarına çevir
    ceviri_tablosu = {
        'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'İ': 'I',
        'ş': 's', 'Ş': 'S',
        'ç': 'c', 'Ç': 'C',
        'ö': 'o', 'Ö': 'O',
        'ü': 'u', 'Ü': 'U',
        'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I',
        'û': 'u', 'Û': 'U'
    }
    for turkce, ingilizce in ceviri_tablosu.items():
        text = text.replace(turkce, ingilizce)
    return text

def create_pdf_report(dataframe, bas_t, bit_t):
    # Orientation 'L' = Landscape (Yatay)
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    
    # 1. RAPOR BAŞLIĞI
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(44, 62, 80)
    
    # Başlık için tarihleri formatla
    baslik_bas = tarih_formatla(bas_t)
    baslik_bit = tarih_formatla(bit_t)
    
    baslik = f"BEYKOZ HABER RAPORU ({baslik_bas} - {baslik_bit})"
    pdf.cell(0, 10, tr_karakter_duzelt(baslik), ln=True, align='C')
    pdf.ln(5)

    # Veri kontrolü
    if dataframe.empty:
        pdf.set_font("Arial", 'I', 12)
        pdf.cell(0, 10, "Bu tarih aralığında kayıt bulunamadı.", ln=True, align='C')
        return pdf.output(dest='S').encode('latin-1', 'ignore')

    # 2. TABLO BAŞLIKLARI (RENKLİ)
    w_tarih = 25
    w_mudurluk = 50
    w_kaynak = 35
    w_sayi = 15
    w_ayrinti = 150 

    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(41, 128, 185)  # Mavi tonu
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(50, 50, 100)

    header_h = 8
    pdf.cell(w_tarih, header_h, "Tarih", 1, 0, 'C', fill=True)
    pdf.cell(w_mudurluk, header_h, "Mudurluk", 1, 0, 'C', fill=True)
    pdf.cell(w_kaynak, header_h, "Kaynak", 1, 0, 'C', fill=True)
    pdf.cell(w_sayi, header_h, "Adet", 1, 0, 'C', fill=True)
    pdf.cell(w_ayrinti, header_h, "Ayrinti / Sikayet", 1, 1, 'C', fill=True)

    # 3. TABLO İÇERİĞİ (ZEBRA DESENLİ)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(0, 0, 0)
    
    fill = False
    # Tarih sütununu datetime'a çevir ve sırala
    try:
        dataframe_sorted = dataframe.copy()
        dataframe_sorted['Tarih'] = pd.to_datetime(dataframe_sorted['Tarih'])
        dataframe_sorted = dataframe_sorted.sort_values(by=['Tarih', 'Müdürlük'])
    except:
        dataframe_sorted = dataframe.sort_values(by=['Tarih', 'Müdürlük'])

    for i, row in dataframe_sorted.iterrows():
        # Tarih formatla
        tarih_val = row['Tarih']
        if isinstance(tarih_val, pd.Timestamp):
            tarih_formatted = tarih_val.strftime('%d.%m.%Y')
        elif isinstance(tarih_val, datetime):
            tarih_formatted = tarih_val.strftime('%d.%m.%Y')
        else:
            # String ise
            try:
                tarih_obj = datetime.strptime(str(tarih_val), '%Y-%m-%d')
                tarih_formatted = tarih_obj.strftime('%d.%m.%Y')
            except:
                try:
                    tarih_obj = datetime.strptime(str(tarih_val), '%d.%m.%Y')
                    tarih_formatted = tarih_obj.strftime('%d.%m.%Y')
                except:
                    tarih_formatted = str(tarih_val)[:10]
        
        tarih = tr_karakter_duzelt(tarih_formatted)
        mudurluk = tr_karakter_duzelt(str(row['Müdürlük']))
        kaynak = tr_karakter_duzelt(str(row['Haber_Kaynagi']))
        sayi = str(row['Sayı'])
        ayrinti = tr_karakter_duzelt(str(row['Ayrıntı']))

        # V1.3 GÜNCELLEME: Satır yüksekliği metne göre otomatik
        # Her satır yaklaşık 95 karakter alıyor, satır başına 6mm yükseklik
        satir_sayisi = max(1, len(ayrinti) // 95 + 1) 
        h_satir = 6 * satir_sayisi

        # Sayfa sonu kontrolü
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

        # Zebra deseni
        if fill:
            pdf.set_fill_color(235, 245, 251)  # Açık mavi
        else:
            pdf.set_fill_color(255, 255, 255)

        x_baslangic = pdf.get_x()
        y_baslangic = pdf.get_y()

        # Tarih hücresi
        pdf.cell(w_tarih, h_satir, tarih, 1, 0, 'C', fill=True)
        
        # Müdürlük hücresi (küçük font gerekirse)
        if len(mudurluk) > 25: 
             pdf.set_font("Arial", size=7)
             pdf.cell(w_mudurluk, h_satir, mudurluk, 1, 0, 'L', fill=True)
             pdf.set_font("Arial", size=9)
        else:
             pdf.cell(w_mudurluk, h_satir, mudurluk, 1, 0, 'L', fill=True)
             
        # Kaynak hücresi
        pdf.cell(w_kaynak, h_satir, kaynak, 1, 0, 'C', fill=True)
        
        # Sayı hücresi
        pdf.cell(w_sayi, h_satir, sayi, 1, 0, 'C', fill=True)
        
        # Ayrıntı hücresi (multi-cell) - V1.3: Otomatik yükseklik
        x_ayrinti = x_baslangic + w_tarih + w_mudurluk + w_kaynak + w_sayi
        pdf.set_xy(x_ayrinti, y_baslangic)
        pdf.multi_cell(w_ayrinti, 6, ayrinti, border=1, align='L', fill=True)
        
        # Yeni satıra geç
        pdf.set_xy(x_baslangic, y_baslangic + h_satir)

        fill = not fill

    # PDF'i bytes olarak döndür
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- CALLBACK FONKSİYONU ---
def kaydet_ve_sifirla():
    secilen_mudurlukler = st.session_state.form_mudurlukler
    if not secilen_mudurlukler:
        st.error("Lütfen en az bir müdürlük seçiniz!")
        return False
    
    # V1.3: Diğer kaynak kontrolü
    kaynak = st.session_state.form_kaynak
    if kaynak == "Diğer":
        diger_kaynak = st.session_state.diger_kaynak.strip()
        if not diger_kaynak:
            st.error("Lütfen 'Diğer' kaynak için açıklama giriniz!")
            return False
        # Diğer kaynağı kullan
        kaynak = diger_kaynak
    
    veri_kaydet_dosyaya(
        st.session_state.form_tarih,
        secilen_mudurlukler,
        kaynak,
        st.session_state.form_sayi,
        st.session_state.form_ayrinti
    )
    st.toast(f"✅ Kayıt Başarılı! ({len(secilen_mudurlukler)} Müdürlük Eklendi)")
    st.session_state.form_sayi = 1
    st.session_state.form_ayrinti = ""
    st.session_state.diger_kaynak = ""  # Diğer kaynağı temizle
    return True

# --- ARAYÜZ ---
st.title("📊 Beykoz Haber Hesapları - Yönetici Paneli")
st.caption("V1.3 - Filtreleme ve Çıktı İyileştirmeleri")

# --- SOL MENÜ: VERİ GİRİŞİ ---
with st.sidebar:
    st.header("📝 Veri Girişi")
    with st.form("giris_formu", clear_on_submit=False):
        st.date_input("Tarih", value=date.today(), format="DD/MM/YYYY", key="form_tarih")
        
        # V1.3: Müdürlük seçimi - MULTISELECT olarak (eski hali)
        st.multiselect(
            "Müdürlükler",
            MUDURLUKLER,
            key="form_mudurlukler",
            placeholder="Müdürlük seçiniz..."
        )
        
        # V1.3: Kaynak seçimi - Diğer için metin kutusu
        kaynak_secim = st.selectbox("Kaynak", HABER_KAYNAKLARI, key="form_kaynak")
        
        # Eğer "Diğer" seçildiyse metin kutusu göster
        if kaynak_secim == "Diğer":
            st.text_input(
                "Diğer Kaynak (Zorunlu)",
                placeholder="Kaynak adını yazınız...",
                key="diger_kaynak"
            )
        
        st.number_input("Sayı", min_value=1, step=1, key="form_sayi")
        st.text_area("Ayrıntı", height=150, placeholder="Şikayet detayları...", key="form_ayrinti")
        
        if st.form_submit_button("💾 Kaydet"):
            if kaydet_ve_sifirla():
                st.rerun()

# --- ANA EKRAN ---
df = veri_yukle()
if not df.empty:
    # Tarih sütununu datetime formatına çevir
    try:
        df['Tarih'] = pd.to_datetime(df['Tarih']).dt.date
    except:
        st.warning("Tarih sütununda format sorunu bulunuyor.")

# FİLTRELER - V1.3: Müdürlük filtresi multiselect olacak
st.markdown("### 🔍 Rapor Filtreleme")
c1, c2, c3, c4 = st.columns(4)
bas = c1.date_input("Başlangıç Tarihi", date.today(), format="DD/MM/YYYY")
bit = c2.date_input("Bitiş Tarihi", date.today(), format="DD/MM/YYYY")

# V1.3: Müdürlük filtresi MULTISELECT olarak (eski hali)
mud_sec = c3.multiselect(
    "Müdürlük Filtresi", 
    MUDURLUKLER, 
    placeholder="Tüm müdürlükler"
)

kaynak_sec = c4.multiselect(
    "Kaynak Filtresi", 
    HABER_KAYNAKLARI, 
    placeholder="Tüm kaynaklar"
)

if not df.empty:
    try:
        mask = (df['Tarih'] >= bas) & (df['Tarih'] <= bit)
        if mud_sec: 
            mask &= df['Müdürlük'].isin(mud_sec)
        if kaynak_sec: 
            mask &= df['Haber_Kaynagi'].isin(kaynak_sec)
        df_filt = df.loc[mask].copy()
    except Exception as e:
        st.error(f"Filtreleme hatası: {e}")
        df_filt = pd.DataFrame()

    if not df_filt.empty:
        # --- 1. LİSTELEME VE DÜZENLEME ---
        st.markdown("---")
        st.subheader("📋 Kayıtlar (Düzenle / Sil)")
        st.info("💡 Tabloyu açarak detayları görebilir ve düzenleyebilirsiniz. Silinecek satırları işaretleyin ve 'Değişiklikleri Kaydet' butonuna tıklayın.")
        
        # Pending changes bildirimi
        if st.session_state.pending_changes:
            st.warning("⚠️ Kaydedilmemiş değişiklikler var! Lütfen 'Değişiklikleri Kaydet' butonuna tıklayın.")
            st.session_state.pending_changes = False

        grouped = df_filt.groupby(['Tarih', 'Müdürlük'])
        
        # Tüm değişiklikleri toplamak için liste
        all_edited_data = {}
        
        for (trh, mud), grup in grouped:
            trh_str = tarih_formatla(trh)
            toplam_sayi = grup['Sayı'].sum()
            
            with st.expander(f"📅 {trh_str}  |  🏢 {mud}  |  Toplam: {toplam_sayi}"):
                # Orijinal indeksleri kaydet
                original_indices = list(grup.index)
                
                # Düzenlenebilir tablo oluştur
                edited_df = st.data_editor(
                    grup[['Tarih', 'Müdürlük', 'Haber_Kaynagi', 'Sayı', 'Ayrıntı']],
                    num_rows="dynamic",
                    key=f"editor_{trh}_{mud}_{len(grup)}",
                    use_container_width=True,
                    hide_index=False,
                    column_config={
                        "Tarih": st.column_config.DateColumn("Tarih", format="DD/MM/YYYY"),
                        "Ayrıntı": st.column_config.TextColumn("Ayrıntı", width="large"),
                        "__index__": st.column_config.NumberColumn("ID", disabled=True)
                    }
                )
                
                # Değişiklikleri session state'e kaydet
                all_edited_data[f"{trh}_{mud}"] = {
                    'original_indices': original_indices,
                    'edited_data': edited_df,
                    'tarih': trh,
                    'mudurluk': mud
                }
        
        # Global Değişiklikleri Kaydet butonu
        if all_edited_data:
            col1, col2, col3 = st.columns([1, 1, 3])
            
            if col1.button("💾 Değişiklikleri Kaydet", type="primary", use_container_width=True):
                try:
                    # Tüm değişiklikleri uygula
                    for key, data in all_edited_data.items():
                        original_indices = data['original_indices']
                        edited_data = data['edited_data']
                        
                        # Orijinal verileri sil
                        df = df.drop(original_indices, errors='ignore')
                        
                        # Düzenlenmiş verileri ekle (eğer boş değilse)
                        if not edited_data.empty:
                            # Tarih formatını koru
                            edited_data['Tarih'] = pd.to_datetime(edited_data['Tarih']).dt.date
                            df = pd.concat([df, edited_data], ignore_index=True)
                    
                    # CSV'ye kaydet
                    df.to_csv(DOSYA_ADI, index=False)
                    st.success("✅ Tüm değişiklikler kaydedildi!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Kaydetme hatası: {str(e)}")
            
            if col2.button("🔄 Değişiklikleri İptal Et", use_container_width=True):
                st.info("Değişiklikler iptal edildi, sayfa yenileniyor...")
                st.rerun()

        # --- 2. ÇIKTI ALMA (EXCEL, HTML ve PDF) ---
        st.markdown("---")
        st.subheader("🖨️ Rapor Çıktısı Al")
        
        # V1.3: "Tarih" olarak değiştirildi (Formatlı yazmıyor)
        tum_sutunlar = ["Tarih", "Müdürlük", "Toplam Sayı", "Kaynak Dağılımı", "Detaylar", "Sonuç"]
        secilen_sutunlar = st.multiselect("Sütun Seçimi", tum_sutunlar, default=tum_sutunlar, placeholder="Sütun seçiniz...")
        
        if secilen_sutunlar:
            ozet_liste = []
            for (trh, mud), grup in df_filt.groupby(['Tarih', 'Müdürlük']):
                toplam, kaynak_txt, detay_txt = ozet_metni_olustur(grup)
                ozet_liste.append({
                    "Tarih": tarih_formatla(trh),  # V1.3: "Tarih (Formatlı)" yerine "Tarih"
                    "Müdürlük": mud,
                    "Toplam Sayı": toplam,
                    "Kaynak Dağılımı": kaynak_txt,
                    "Detaylar": detay_txt,
                    "Sonuç": ""  # Boş Sonuç sütunu
                })
            
            df_ozet = pd.DataFrame(ozet_liste)[secilen_sutunlar]
            
            # Çıktı butonları için 3 sütun oluştur
            col_ex, col_html, col_pdf = st.columns(3)

            # EXCEL (Renkli) - V1.3 GÜNCELLEME: Satır yüksekliği otomatik
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_ozet.to_excel(writer, sheet_name='Rapor', index=False)
                workbook = writer.book
                worksheet = writer.sheets['Rapor']
                
                # Formatlar
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#2c3e50',
                    'font_color': 'white',
                    'border': 1,
                    'align': 'center'
                })
                
                cell_format = workbook.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1
                })
                
                # V1.3 GÜNCELLEME: Detaylar için özel format (satır yüksekliği otomatik)
                detay_format = workbook.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1
                })
                
                sonuc_format = workbook.add_format({
                    'text_wrap': True,
                    'valign': 'top',
                    'border': 1,
                    'bg_color': '#FFF3CD',  # Açık sarı arkaplan
                    'font_color': '#856404'  # Koyu sarı font
                })
                
                # Sütun genişlikleri - Sabit genişlikler
                column_widths = {
                    'A': 20,  # Tarih
                    'B': 30,  # Müdürlük
                    'C': 15,  # Toplam Sayı
                    'D': 30,  # Kaynak Dağılımı
                    'E': 60,  # Detaylar
                    'F': 25   # Sonuç
                }
                
                for col, width in column_widths.items():
                    worksheet.set_column(f'{col}:{col}', width, cell_format)
                
                # Detaylar sütunu için özel format
                if 'Detaylar' in df_ozet.columns:
                    detaylar_index = df_ozet.columns.get_loc('Detaylar')
                    detaylar_col = chr(65 + detaylar_index)
                    worksheet.set_column(f'{detaylar_col}:{detaylar_col}', 60, detay_format)
                
                # Sonuç sütunu için özel format
                if 'Sonuç' in df_ozet.columns:
                    sonuc_index = df_ozet.columns.get_loc('Sonuç')
                    sonuc_col = chr(65 + sonuc_index)
                    worksheet.set_column(f'{sonuc_col}:{sonuc_col}', 25, sonuc_format)
                
                # Başlıkları formatla
                for col_num, value in enumerate(df_ozet.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # V1.3 GÜNCELLEME: Satır yüksekliklerini metne göre otomatik ayarla
                for row_num in range(len(df_ozet)):
                    if 'Detaylar' in df_ozet.columns:
                        detay_metni = str(df_ozet.iloc[row_num]['Detaylar'])
                        # Satır sayısını hesapla (her 100 karakter için 1 satır)
                        satir_sayisi = max(1, len(detay_metni) // 100 + 1)
                        # Satır yüksekliğini ayarla (her satır için 15 birim)
                        worksheet.set_row(row_num + 1, satir_sayisi * 15)
                
            col_ex.download_button(
                "📄 Excel İndir (Sonuçlu)", 
                buffer.getvalue(), 
                f"Rapor_{bas.strftime('%d.%m.%Y')}_{bit.strftime('%d.%m.%Y')}.xlsx", 
                "application/vnd.ms-excel",
                use_container_width=True
            )

            # HTML (Renkli ve Stilize) - V1.3 GÜNCELLEME: Satır yüksekliği otomatik
            df_ozet_html = df_ozet.copy()
            if "Detaylar" in df_ozet_html.columns:
                df_ozet_html["Detaylar"] = df_ozet_html["Detaylar"].str.replace("\n", "<br>")
            
            html_style = """
            <style>
            .report-table {
                width: 100%;
                border-collapse: collapse;
                font-family: Arial, sans-serif;
                font-size: 12px;
                table-layout: fixed;
            }
            .report-table th {
                background-color: #2c3e50;
                color: white;
                padding: 12px;
                text-align: center;
                font-weight: bold;
                border: 1px solid #dee2e6;
            }
            .report-table td {
                padding: 10px;
                border: 1px solid #dee2e6;
                vertical-align: top;
                word-wrap: break-word;
            }
            .report-table tr:nth-child(even) {
                background-color: #f8f9fa;
            }
            .report-table tr:hover {
                background-color: #e9ecef;
            }
            .sonuc-sutunu {
                background-color: #fff3cd !important;
                color: #856404;
                font-weight: bold;
            }
            .tarih-sutunu {
                text-align: center;
                font-weight: bold;
                width: 120px;
            }
            .mudurluk-sutunu {
                width: 180px;
            }
            .sayi-sutunu {
                text-align: center;
                font-weight: bold;
                color: #2c3e50;
                width: 80px;
            }
            .kaynak-sutunu {
                width: 180px;
            }
            .detaylar-sutunu {
                width: 400px;
                min-height: 50px;
                white-space: normal !important;
                word-wrap: break-word;
            }
            .sonuc-sutunu {
                width: 150px;
            }
            </style>
            """
            
            html_table = df_ozet_html.to_html(index=False, escape=False, classes='report-table')
            
            # V1.3 GÜNCELLEME: Tüm sütunlara class ekle
            html_table = html_table.replace('<td>Tarih</td>', '<td class="tarih-sutunu">Tarih</td>')
            html_table = html_table.replace('<td>Müdürlük</td>', '<td class="mudurluk-sutunu">Müdürlük</td>')
            html_table = html_table.replace('<td>Toplam Sayı</td>', '<td class="sayi-sutunu">Toplam Sayı</td>')
            html_table = html_table.replace('<td>Kaynak Dağılımı</td>', '<td class="kaynak-sutunu">Kaynak Dağılımı</td>')
            html_table = html_table.replace('<td>Detaylar</td>', '<td class="detaylar-sutunu">Detaylar</td>')
            html_table = html_table.replace('<td>Sonuç</td>', '<td class="sonuc-sutunu">Sonuç</td>')
            
            # Data hücrelerine class ekle
            rows = html_table.split('<tr>')
            for i in range(1, len(rows)):
                cells = rows[i].split('<td>')
                if len(cells) > 1:
                    # Tarih
                    cells[1] = cells[1].replace('>', ' class="tarih-sutunu">', 1)
                    # Müdürlük
                    if len(cells) > 2:
                        cells[2] = cells[2].replace('>', ' class="mudurluk-sutunu">', 1)
                    # Toplam Sayı
                    if len(cells) > 3:
                        cells[3] = cells[3].replace('>', ' class="sayi-sutunu">', 1)
                    # Kaynak Dağılımı
                    if len(cells) > 4:
                        cells[4] = cells[4].replace('>', ' class="kaynak-sutunu">', 1)
                    # Detaylar
                    if len(cells) > 5:
                        cells[5] = cells[5].replace('>', ' class="detaylar-sutunu">', 1)
                    # Sonuç
                    if len(cells) > 6:
                        cells[6] = cells[6].replace('>', ' class="sonuc-sutunu">', 1)
                
                rows[i] = '<td>'.join(cells)
            
            html_table = '<tr>'.join(rows)
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Beykoz Raporu</title>
                {html_style}
            </head>
            <body>
                <h2 style="text-align: center; color: #2c3e50;">Beykoz Haber Raporu</h2>
                <h4 style="text-align: center; color: #34495e;">({tarih_formatla(bas)} - {tarih_formatla(bit)})</h4>
                <div style="margin: 20px; text-align: center;">
                    <p><strong>Versiyon:</strong> V1.3 - Filtreleme ve Çıktı İyileştirmeleri</p>
                    <p><strong>Toplam Kayıt:</strong> {len(df_filt)} | <strong>Toplam Şikayet:</strong> {df_filt['Sayı'].sum()}</p>
                </div>
                <br>
                {html_table}
            </body>
            </html>
            """
            
            col_html.download_button(
                "🌐 HTML İndir (Sonuçlu)", 
                html_content, 
                f"Rapor_{bas.strftime('%d.%m.%Y')}_{bit.strftime('%d.%m.%Y')}.html", 
                "text/html",
                use_container_width=True
            )

            # PDF
            @st.cache_data
            def create_and_cache_pdf(dataframe, bas_t, bit_t):
                """PDF oluştur ve cache'le"""
                try:
                    return create_pdf_report(dataframe.copy(), bas_t, bit_t)
                except Exception as e:
                    st.error(f"PDF oluşturma hatası: {e}")
                    return None
            
            pdf_bytes = create_and_cache_pdf(df_filt, bas, bit)
            
            if pdf_bytes:
                col_pdf.download_button(
                    "📕 PDF İndir (Detaylı)", 
                    pdf_bytes, 
                    f"Rapor_{bas.strftime('%d.%m.%Y')}_{bit.strftime('%d.%m.%Y')}.pdf", 
                    "application/pdf",
                    use_container_width=True
                )
            else:
                col_pdf.error("PDF oluşturulamadı")

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