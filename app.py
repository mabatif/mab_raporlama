import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io
import time
import base64
import os

# ==== 2. GSPREAD KONTROLÜ ====
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    st.warning("⚠️ Google Sheets bağlantısı için paketler yükleniyor...")
    st.info("""
    **Gerekli paketler:**
    ```
    gspread==5.11.0
    oauth2client==4.1.3
    google-auth==2.23.0
    ```
    Lütfen 'gereksinimler.txt' dosyasını kontrol edin.
    """)

# ==== 3. GOOGLE SHEETS AYARLARI ====
if GSPREAD_AVAILABLE:
    try:
        GOOGLE_SHEET_ID = st.secrets["google"]["sheet_id"]
        SHEET_NAME = "Beykoz_Verileri"
    except:
        GOOGLE_SHEET_ID = None
        SHEET_NAME = "Beykoz_Verileri"
else:
    GOOGLE_SHEET_ID = None

# ==== 3. GOOGLE SHEETS BAĞLANTISI ====
@st.cache_resource
def get_google_sheet():
    """Google Sheets bağlantısını kur"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        # Streamlit Secrets'tan kimlik bilgilerini al
        creds_dict = dict(st.secrets["google"]["service_account"])
        
        # Kimlik bilgilerini oluştur
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=scopes
        )
        
        # Gspread istemcisi
        gc = gspread.authorize(credentials)
        
        # Sheet'i aç
        sheet = gc.open_by_key(GOOGLE_SHEET_ID)
        
        # Worksheet kontrolü
        try:
            worksheet = sheet.worksheet(SHEET_NAME)
        except gspread.exceptions.WorksheetNotFound:
            # Yeni sheet oluştur
            worksheet = sheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=10)
            # Başlıkları ekle
            headers = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
            worksheet.append_row(headers)
        
        return worksheet
    
    except Exception as e:
        st.error(f"Google Sheets bağlantı hatası: {str(e)[:100]}")
        return None

# ==== 4. VERİ YÜKLEME FONKSİYONU ====
def veri_yukle():
    """Google Sheets'ten verileri yükle"""
    try:
        worksheet = get_google_sheet()
        if worksheet is None:
            return pd.DataFrame()
        
        # Tüm verileri al
        records = worksheet.get_all_records()
        
        if records:
            df = pd.DataFrame(records)
            
            # Tarih sütununu düzelt
            if 'Tarih' in df.columns and not df.empty:
                df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
            
            return df
        else:
            # Boş DataFrame döndür
            kolonlar = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
            return pd.DataFrame(columns=kolonlar)
    
    except Exception as e:
        st.error(f"Veri yükleme hatası: {e}")
        # Geçici olarak session state kullan
        if "gecici_veriler" not in st.session_state:
            kolonlar = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
            st.session_state.gecici_veriler = pd.DataFrame(columns=kolonlar)
        
        return st.session_state.gecici_veriler

# ==== 5. VERİ KAYDETME FONKSİYONU ====
def veri_kaydet(df):
    """Verileri Google Sheets'e kaydet"""
    try:
        worksheet = get_google_sheet()
        if worksheet is None:
            return False
        
        # DataFrame'i temizle
        df_copy = df.copy()
        
        # Tarih sütununu string'e çevir
        if 'Tarih' in df_copy.columns:
            df_copy['Tarih'] = df_copy['Tarih'].astype(str)
        
        # NaN değerleri boş string yap
        df_copy = df_copy.fillna('')
        
        # Tüm verileri temizle ve yeniden yaz
        worksheet.clear()
        
        # Başlıkları ekle
        headers = list(df_copy.columns)
        worksheet.append_row(headers)
        
        # Verileri ekle (batch halinde)
        if not df_copy.empty:
            records = df_copy.values.tolist()
            # Büyük veriler için batch ekleme
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                worksheet.append_rows(batch, value_input_option='USER_ENTERED')
        
        return True
    
    except Exception as e:
        st.error(f"Kaydetme hatası: {e}")
        # Geçici olarak session state'e kaydet
        st.session_state.gecici_veriler = df.copy()
        return False

# ==== 6. YENİ KAYIT EKLEME ====
def yeni_kayit_ekle(tarih, mudurlukler, kaynak, sayi, ayrinti):
    """Yeni kayıt ekle ve Google Sheets'e kaydet"""
    try:
        # Mevcut verileri yükle
        df = veri_yukle()
        
        # Yeni kayıtları oluştur
        yeni_kayitlar = []
        for mudurluk in mudurlukler:
            yeni_kayit = {
                "Tarih": tarih,
                "Müdürlük": mudurluk,
                "Haber_Kaynagi": kaynak,
                "Sayı": sayi,
                "Ayrıntı": ayrinti,
                "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            yeni_kayitlar.append(yeni_kayit)
        
        # Yeni kayıtları DataFrame'e ekle
        yeni_df = pd.DataFrame(yeni_kayitlar)
        df = pd.concat([df, yeni_df], ignore_index=True)
        
        # Google Sheets'e kaydet
        if veri_kaydet(df):
            return len(yeni_kayitlar)
        else:
            return 0
    
    except Exception as e:
        st.error(f"Kayıt ekleme hatası: {e}")
        return 0

# ==== 7. ŞİFRE KONTROL SİSTEMİ ====
def giris_kontrol():
    """Güvenli kullanıcı girişi"""
    
    if "giris_yapildi" in st.session_state and st.session_state.giris_yapildi:
        return True
    
    # GİRİŞ EKRANI
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 40px;
        border-radius: 15px;
        background: white;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown('<h2 style="text-align: center;">🔐 BEYKOZ HABER SİSTEMİ</h2>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #666;">Google Sheets Entegrasyonlu</p>', unsafe_allow_html=True)
        
        kullanici = st.text_input("**Kullanıcı Adı**", key="login_user")
        sifre = st.text_input("**Şifre**", type="password", key="login_pass")
        
        if st.button("**GİRİŞ YAP**", type="primary", use_container_width=True):
            if "users" in st.secrets and kullanici in st.secrets["users"]:
                kullanici_bilgisi = st.secrets["users"][kullanici]
                
                if sifre == kullanici_bilgisi["password"]:
                    st.session_state.giris_yapildi = True
                    st.session_state.kullanici_adi = kullanici
                    st.session_state.kullanici_rol = kullanici_bilgisi["role"]
                    st.session_state.kullanici_isim = kullanici_bilgisi["name"]
                    st.session_state.giris_zamani = datetime.now()
                    
                    st.success(f"✅ Hoş geldiniz, {kullanici_bilgisi['name']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre!")
            else:
                st.error("❌ Kullanıcı bulunamadı!")
        
        st.markdown("---")
        st.caption("**Google Sheets ile kalıcı veri depolama**")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False

# ==== 8. GİRİŞ KONTROLÜ ====
if not giris_kontrol():
    st.stop()

# ==== 9. SAYFA AYARLARI ====
st.set_page_config(
    page_title="Beykoz Haber Takip - Google Sheets",
    page_icon="📊",
    layout="wide"
)

# ==== 10. ÇIKIŞ BUTONU ====
def cikis_butonu():
    with st.sidebar:
        if st.session_state.giris_yapildi:
            st.markdown("---")
            st.write(f"**👤 {st.session_state.kullanici_isim}**")
            st.write(f"Rol: {st.session_state.kullanici_rol}")
            
            # Google Sheets durumu
            try:
                df = veri_yukle()
                st.caption(f"📊 Google Sheets'te {len(df)} kayıt")
            except:
                st.caption("📊 Veriler yükleniyor...")
            
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                st.session_state.giris_yapildi = False
                st.rerun()

# ==================== SİSTEM AYARLARI ====================

MUDURLUKLER = [
    # ÖNCELİKLİ MÜDÜRLÜKLER
    "Fen İşleri Müdürlüğü",
    "Temizlik İşleri Müdürlüğü", 
    "Zabıta Müdürlüğü",
    "İşletme ve İştirakler Müdürlüğü",
    "Özel Kalem Müdürlüğü",
    "Kültür ve Sosyal İşler Müdürlüğü",
    
    # DİĞER MÜDÜRLÜKLER
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
    "Beykoz Anlık", 
    "Beykoz Burada", 
    "Beykoz Duysun", 
    "Beykoz Güncel", 
    "Diğer"
]

# ==================== ANA UYGULAMA ====================

st.title("📊 BEYKOZ HABER TAKİP SİSTEMİ")
st.markdown("🌐 **Google Sheets Entegrasyonu Aktif** - Verileriniz güvende!")
st.markdown("---")

# YÜKLEME DURUMU
with st.spinner("Google Sheets'ten veriler yükleniyor..."):
    df = veri_yukle()

if df is None or df.empty:
    st.info("📭 Henüz kayıt yok. İlk kaydınızı ekleyin!")
else:
    st.success(f"✅ Google Sheets'ten {len(df)} kayıt yüklendi!")

# SİDEBAR
with st.sidebar:
    st.header("📝 Yeni Kayıt")
    
    with st.form("yeni_kayit", border=True):
        # Form alanları
        kayit_tarihi = st.date_input("📅 Tarih", value=date.today(), format="DD/MM/YYYY")
        
        secilen_mudurlukler = st.multiselect(
            "🏢 Müdürlükler", 
            MUDURLUKLER, 
            placeholder="Seçiniz..."
        )
        
        kaynak = st.selectbox("📱 Kaynak", HABER_KAYNAKLARI)
        
        if kaynak == "Diğer":
            diger_kaynak = st.text_input("✏️ Kaynak Adı", placeholder="Yazın...")
            if diger_kaynak:
                kaynak = diger_kaynak
        
        sayi = st.number_input("🔢 Sayı", min_value=1, value=1)
        
        ayrinti = st.text_area("📝 Ayrıntı", height=120, placeholder="Detaylı açıklama...")
        
        col1, col2 = st.columns(2)
        with col1:
            kaydet_btn = st.form_submit_button("💾 KAYDET", type="primary", use_container_width=True)
        with col2:
            temizle_btn = st.form_submit_button("🔄 TEMİZLE", type="secondary", use_container_width=True)
        
        if kaydet_btn:
            if not secilen_mudurlukler:
                st.error("❌ Lütfen en az bir müdürlük seçin!")
            elif not ayrinti.strip():
                st.error("❌ Lütfen ayrıntı girin!")
            else:
                with st.spinner("Google Sheets'e kaydediliyor..."):
                    eklenen = yeni_kayit_ekle(kayit_tarihi, secilen_mudurlukler, kaynak, sayi, ayrinti)
                
                if eklenen > 0:
                    st.success(f"✅ {eklenen} kayıt Google Sheets'e eklendi!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Kayıt eklenemedi!")
        
        if temizle_btn:
            st.rerun()
    
    st.markdown("---")
    
    # GOOGLE SHEETS YÖNETİMİ
    st.header("📁 Google Sheets")
    
    # Sheets bağlantı linki
    if "google" in st.secrets and "sheet_id" in st.secrets["google"]:
        sheet_id = st.secrets["google"]["sheet_id"]
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        st.markdown(f"[📎 Sheets'e Git]({sheet_url})", unsafe_allow_html=True)
    
    # VERİ İNDİR
    if not df.empty:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="beykoz_verileri_{date.today()}.csv">📥 Tüm Verileri İndir (CSV)</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    # VERİ YÜKLE
    st.markdown("---")
    st.subheader("📤 CSV Yükle")
    
    yuklenen_dosya = st.file_uploader("CSV dosyası seç", type=['csv'])
    if yuklenen_dosya is not None:
        try:
            yeni_veriler = pd.read_csv(yuklenen_dosya, encoding='utf-8-sig')
            
            # Gerekli kolonları kontrol et
            gerekli_kolonlar = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı"]
            
            if all(kolon in yeni_veriler.columns for kolon in gerekli_kolonlar):
                # Mevcut verilerle birleştir
                mevcut_df = veri_yukle()
                birlesik_df = pd.concat([mevcut_df, yeni_veriler], ignore_index=True)
                
                with st.spinner("Google Sheets'e yükleniyor..."):
                    if veri_kaydet(birlesik_df):
                        st.success(f"✅ {len(yeni_veriler)} kayıt yüklendi!")
                        st.rerun()
                    else:
                        st.error("❌ Yükleme başarısız!")
            else:
                st.error("❌ CSV formatı uygun değil!")
                st.write("Gerekli kolonlar:", gerekli_kolonlar)
                
        except Exception as e:
            st.error(f"❌ Yükleme hatası: {e}")
    
    # VERİ TEMİZLEME (sadece admin)
    if st.session_state.kullanici_rol == "admin":
        st.markdown("---")
        st.subheader("⚠️ Yönetici Araçları")
        
        if st.button("🗑️ Tüm Verileri Temizle", type="secondary", use_container_width=True):
            onay = st.checkbox("EMİN MİSİNİZ? Tüm veriler silinecek!")
            if onay:
                kolonlar = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
                bos_df = pd.DataFrame(columns=kolonlar)
                
                with st.spinner("Google Sheets temizleniyor..."):
                    if veri_kaydet(bos_df):
                        st.success("✅ Tüm veriler temizlendi!")
                        st.rerun()
                    else:
                        st.error("❌ Temizleme başarısız!")

# ANA SAYFA İÇERİĞİ
if not df.empty:
    # FİLTRELEME PANELİ
    st.subheader("🔍 Filtrele")
    
    filt_col1, filt_col2, filt_col3, filt_col4 = st.columns(4)
    
    with filt_col1:
        bas_tarih = st.date_input("Başlangıç", 
                                 value=date.today() - timedelta(days=30), 
                                 format="DD/MM/YYYY",
                                 key="bas_tarih")
    
    with filt_col2:
        bit_tarih = st.date_input("Bitiş", 
                                 value=date.today(), 
                                 format="DD/MM/YYYY",
                                 key="bit_tarih")
    
    with filt_col3:
        filt_mudurluk = st.multiselect("Müdürlük", 
                                      MUDURLUKLER, 
                                      placeholder="Tümü",
                                      key="filt_mud")
    
    with filt_col4:
        filt_kaynak = st.multiselect("Kaynak", 
                                    HABER_KAYNAKLARI, 
                                    placeholder="Tümü",
                                    key="filt_kaynak")
    
    # Filtre uygula
    if not df.empty and 'Tarih' in df.columns:
        try:
            # Tarih filtresi
            mask = (df['Tarih'] >= bas_tarih) & (df['Tarih'] <= bit_tarih)
            
            # Müdürlük filtresi
            if filt_mudurluk:
                mask &= df['Müdürlük'].isin(filt_mudurluk)
            
            # Kaynak filtresi
            if filt_kaynak:
                mask &= df['Haber_Kaynagi'].isin(filt_kaynak)
            
            filtrelenmis_df = df[mask].copy()
            
        except Exception as e:
            st.error(f"Filtreleme hatası: {e}")
            filtrelenmis_df = df.copy()
    else:
        filtrelenmis_df = df.copy()
    
    # İSTATİSTİK KARTLARI
    st.markdown("---")
    
    ist1, ist2, ist3, ist4 = st.columns(4)
    
    with ist1:
        toplam_kayit = len(filtrelenmis_df)
        toplam_sayi = filtrelenmis_df['Sayı'].sum()
        st.metric("📊 Toplam", toplam_sayi, f"{toplam_kayit} kayıt")
    
    with ist2:
        mud_sayi = filtrelenmis_df['Müdürlük'].nunique()
        st.metric("🏢 Müdürlük", mud_sayi)
    
    with ist3:
        kaynak_sayi = filtrelenmis_df['Haber_Kaynagi'].nunique()
        st.metric("📱 Kaynak", kaynak_sayi)
    
    with ist4:
        gun_sayi = filtrelenmis_df['Tarih'].nunique()
        st.metric("📅 Gün", gun_sayi)
    
    # VERİ TABLOSU
    st.markdown("---")
    st.subheader("📋 Kayıtlar")
    
    # Düzenlenebilir tablo
    duzenlenen_df = st.data_editor(
        filtrelenmis_df[['Tarih', 'Müdürlük', 'Haber_Kaynagi', 'Sayı', 'Ayrıntı']],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Tarih": st.column_config.DateColumn("Tarih", format="DD/MM/YYYY"),
            "Müdürlük": st.column_config.SelectboxColumn("Müdürlük", options=MUDURLUKLER),
            "Haber_Kaynagi": st.column_config.TextColumn("Kaynak"),
            "Sayı": st.column_config.NumberColumn("Sayı", min_value=1),
            "Ayrıntı": st.column_config.TextColumn("Ayrıntı", width="large")
        }
    )
    
    # Değişiklikleri kaydet butonu
    if st.button("💾 Değişiklikleri Google Sheets'e Kaydet", type="primary", use_container_width=True):
        with st.spinner("Google Sheets güncelleniyor..."):
            # Orijinal df'yi güncelle
            for idx in filtrelenmis_df.index:
                if idx < len(duzenlenen_df):
                    df.loc[idx, 'Tarih'] = duzenlenen_df.iloc[idx]['Tarih']
                    df.loc[idx, 'Müdürlük'] = duzenlenen_df.iloc[idx]['Müdürlük']
                    df.loc[idx, 'Haber_Kaynagi'] = duzenlenen_df.iloc[idx]['Haber_Kaynagi']
                    df.loc[idx, 'Sayı'] = duzenlenen_df.iloc[idx]['Sayı']
                    df.loc[idx, 'Ayrıntı'] = duzenlenen_df.iloc[idx]['Ayrıntı']
            
            # Google Sheets'e kaydet
            if veri_kaydet(df):
                st.success("✅ Değişiklikler Google Sheets'e kaydedildi!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Kaydetme başarısız!")
    
    # EXCEL İNDİR
    st.markdown("---")
    st.subheader("📈 Raporlar")
    
    if not filtrelenmis_df.empty:
        # Excel oluştur
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            filtrelenmis_df.to_excel(writer, index=False, sheet_name='Beykoz_Raporu')
            
            workbook = writer.book
            worksheet = writer.sheets['Beykoz_Raporu']
            
            # Format
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#2c3e50',
                'font_color': 'white',
                'border': 1
            })
            
            # Sütun genişlikleri
            worksheet.set_column('A:A', 12)  # Tarih
            worksheet.set_column('B:B', 25)  # Müdürlük
            worksheet.set_column('C:C', 20)  # Kaynak
            worksheet.set_column('D:D', 10)  # Sayı
            worksheet.set_column('E:E', 50)  # Ayrıntı
            worksheet.set_column('F:F', 20)  # Kayıt Zamanı
            
            # Başlık formatı
            for col_num, value in enumerate(filtrelenmis_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        
        excel_data = excel_buffer.getvalue()
        
        # İndirme butonu
        st.download_button(
            label="📥 Excel Raporu İndir",
            data=excel_data,
            file_name=f"beykoz_rapor_{date.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
    
    # GRAFİKLER
    st.markdown("---")
    st.subheader("📊 Görselleştirme")
    
    graf_col1, graf_col2 = st.columns(2)
    
    with graf_col1:
        st.caption("🏢 Müdürlük Dağılımı")
        if not filtrelenmis_df.empty:
            mud_dagilim = filtrelenmis_df.groupby('Müdürlük')['Sayı'].sum().sort_values(ascending=True)
            if not mud_dagilim.empty:
                st.bar_chart(mud_dagilim, use_container_width=True)
    
    with graf_col2:
        st.caption("📅 Tarihsel Dağılım")
        if not filtrelenmis_df.empty:
            try:
                # Tarih formatını düzelt
                tarih_df = filtrelenmis_df.copy()
                tarih_df['Tarih'] = pd.to_datetime(tarih_df['Tarih'])
                gunluk_dagilim = tarih_df.groupby(tarih_df['Tarih'].dt.date)['Sayı'].sum()
                if not gunluk_dagilim.empty:
                    st.line_chart(gunluk_dagilim, use_container_width=True)
            except Exception as e:
                st.info("Grafik oluşturulamadı")

else:
    # VERİ YOKSA
    st.info("""
    📭 **Henüz kayıt bulunmuyor.**
    
    İlk kaydınızı eklemek için:
    1. Sol taraftaki formu doldurun
    2. **💾 KAYDET** butonuna tıklayın
    3. Veriler otomatik Google Sheets'e kaydedilecek
    """)
    
    # Hızlı örnek veri butonu
    if st.button("🚀 Örnek Veri Oluştur ve Test Et"):
        ornek_veriler = [
            {
                "Tarih": date.today(),
                "Müdürlük": "Fen İşleri Müdürlüğü",
                "Haber_Kaynagi": "Beykoz Anlık",
                "Sayı": 3,
                "Ayrıntı": "Yol çalışması hakkında şikayetler",
                "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "Tarih": date.today() - timedelta(days=1),
                "Müdürlük": "Temizlik İşleri Müdürlüğü",
                "Haber_Kaynagi": "Beykoz Burada",
                "Sayı": 2,
                "Ayrıntı": "Çöp toplama saatleri ile ilgili öneriler",
                "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
        
        ornek_df = pd.DataFrame(ornek_veriler)
        
        with st.spinner("Google Sheets'e kaydediliyor..."):
            if veri_kaydet(ornek_df):
                st.success("✅ Örnek veriler Google Sheets'e eklendi!")
                st.rerun()
            else:
                st.error("❌ Örnek veri eklenemedi!")

# ==== ÇIKIŞ BUTONU ====
cikis_butonu()

# ALT BİLGİ
st.markdown("---")
st.caption(f"© 2026 MAB Tarafından Geliştirildi. • V2.0 Google Sheets Entegrasyonu • Son güncelleme: {datetime.now().strftime('%H:%M')}")

