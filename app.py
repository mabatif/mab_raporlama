import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io
import time
import base64
import os
import sys

# ==================== PAKET KONTROLÜ ====================
st.set_page_config(
    page_title="Beykoz Haber Takip",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paket kontrolü için özel CSS
st.markdown("""
<style>
.package-check {
    padding: 20px;
    border-radius: 10px;
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)

# Paketleri kontrol et
try:
    import gspread
    from google.oauth2.service_account import Credentials
    PACKAGES_OK = True
except ImportError as e:
    PACKAGES_OK = False
    
    with st.container():
        st.markdown('<div class="package-check">', unsafe_allow_html=True)
        st.error("⚠️ **PAKET HATASI**")
        st.write(f"Hata: `{str(e)}`")
        
        st.markdown("""
        ### 🚨 Çözüm Adımları:
        
        1. **GitHub'da `requirements.txt` dosyası olduğundan emin olun**
        2. **İçeriği şöyle olmalı:**
        ```
        streamlit==1.28.0
        pandas==2.1.0
        gspread==5.11.0
        oauth2client==4.1.3
        google-auth==2.23.0
        ```
        3. **Streamlit Cloud → Settings → Dependencies kontrol edin**
        4. **Redeploy yapın**
        """)
        
        # Paket yükleme butonu (sadece gösterim)
        if st.button("🔄 Paketleri Kontrol Et"):
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== GÜVENLİK SİSTEMİ ====================
def giris_kontrol():
    """Basit giriş kontrolü"""
    
    if "giris_yapildi" in st.session_state and st.session_state.giris_yapildi:
        return True
    
    # GİRİŞ EKRANI
    st.title("🔐 Beykoz Haber Takip Sistemi")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("### Giriş Yap")
            
            kullanici = st.text_input("Kullanıcı Adı")
            sifre = st.text_input("Şifre", type="password")
            
            if st.button("Giriş Yap", type="primary", use_container_width=True):
                try:
                    if "users" in st.secrets and kullanici in st.secrets["users"]:
                        if sifre == st.secrets["users"][kullanici]["password"]:
                            st.session_state.giris_yapildi = True
                            st.session_state.kullanici = kullanici
                            st.session_state.rol = st.secrets["users"][kullanici]["role"]
                            st.session_state.isim = st.secrets["users"][kullanici]["name"]
                            st.success("Giriş başarılı!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Hatalı şifre!")
                    else:
                        st.error("Kullanıcı bulunamadı!")
                except Exception as e:
                    st.error(f"Giriş hatası: {e}")
            
            st.markdown("---")
            st.caption("**Test Kullanıcıları:**")
            st.caption("- admin / Beykoz2024!")
            st.caption("- editor / Edit123!")
    
    return False

# Giriş kontrolünü çalıştır
if not giris_kontrol():
    st.stop()

# ==================== VERİTABANI SİSTEMİ ====================
def veri_yukle():
    """Akıllı veri yükleme: Önce Google Sheets, sonra local"""
    
    # 1. GOOGLE SHEETS DENE
    if PACKAGES_OK and "google" in st.secrets and "sheet_id" in st.secrets["google"]:
        try:
            df = google_sheets_yukle()
            if df is not None and not df.empty:
                st.sidebar.success("✅ Google Sheets bağlantısı başarılı!")
                return df
        except Exception as e:
            st.sidebar.warning(f"Google Sheets: {str(e)[:50]}...")
    
    # 2. LOCAL CSV KULLAN
    return local_csv_yukle()

def google_sheets_yukle():
    """Google Sheets'ten veri yükle"""
    try:
        # Credentials
        creds_dict = dict(st.secrets["google"]["service_account"])
        
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        # Gspread
        gc = gspread.authorize(credentials)
        
        # Sheet
        sheet = gc.open_by_key(st.secrets["google"]["sheet_id"])
        
        # Worksheet (yoksa oluştur)
        try:
            worksheet = sheet.worksheet("Beykoz_Verileri")
        except:
            worksheet = sheet.add_worksheet("Beykoz_Verileri", 1000, 10)
            worksheet.append_row(["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"])
        
        # Verileri al
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)
        
        if 'Tarih' in df.columns and not df.empty:
            df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
        
        return df
    
    except Exception as e:
        raise e

def local_csv_yukle():
    """Local CSV'den veri yükle"""
    CSV_DOSYASI = "beykoz_veriler.csv"
    
    if os.path.exists(CSV_DOSYASI):
        df = pd.read_csv(CSV_DOSYASI, encoding='utf-8-sig')
        
        if 'Tarih' in df.columns and not df.empty:
            df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
        
        return df
    else:
        # Yeni boş veritabanı
        kolonlar = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
        df = pd.DataFrame(columns=kolonlar)
        df.to_csv(CSV_DOSYASI, index=False, encoding='utf-8-sig')
        return df

def veri_kaydet(df):
    """Verileri kaydet (hem local hem Google Sheets)"""
    
    # 1. HER ZAMAN LOCAL'E KAYDET
    CSV_DOSYASI = "beykoz_veriler.csv"
    df.to_csv(CSV_DOSYASI, index=False, encoding='utf-8-sig')
    
    # 2. GOOGLE SHEETS'E KAYDETMEYİ DENE
    if PACKAGES_OK and "google" in st.secrets:
        try:
            google_sheets_kaydet(df)
            return "google"
        except:
            return "local"
    
    return "local"

def google_sheets_kaydet(df):
    """Google Sheets'e kaydet"""
    try:
        # Credentials
        creds_dict = dict(st.secrets["google"]["service_account"])
        
        credentials = Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        
        # Gspread
        gc = gspread.authorize(credentials)
        
        # Sheet
        sheet = gc.open_by_key(st.secrets["google"]["sheet_id"])
        
        # Worksheet
        try:
            worksheet = sheet.worksheet("Beykoz_Verileri")
        except:
            worksheet = sheet.add_worksheet("Beykoz_Verileri", 1000, 10)
        
        # Temizle ve yeniden yaz
        worksheet.clear()
        
        # Başlıklar
        headers = list(df.columns)
        worksheet.append_row(headers)
        
        # Veriler
        if not df.empty:
            records = df.values.tolist()
            worksheet.append_rows(records)
        
        return True
    
    except Exception as e:
        raise e

# ==================== ANA UYGULAMA ====================
st.title("📊 BEYKOZ HABER TAKİP SİSTEMİ")

# Durum göstergesi
if PACKAGES_OK:
    st.success("✅ Tüm paketler yüklü")
else:
    st.warning("⚠️ Bazı paketler eksik - Local modda çalışıyor")

st.markdown("---")

# Verileri yükle
with st.spinner("Veriler yükleniyor..."):
    df = veri_yukle()

# SİDEBAR
with st.sidebar:
    st.header(f"👤 {st.session_state.isim}")
    st.caption(f"Rol: {st.session_state.rol}")
    
    st.markdown("---")
    
    # YENİ KAYIT FORMU
    st.header("📝 Yeni Kayıt")
    
    with st.form("yeni_kayit_formu"):
        tarih = st.date_input("Tarih", value=date.today())
        
        müdürlükler = [
            "Fen İşleri Müdürlüğü",
            "Temizlik İşleri Müdürlüğü", 
            "Zabıta Müdürlüğü",
            "İşletme ve İştirakler Müdürlüğü",
            "Özel Kalem Müdürlüğü",
            "Diğer"
        ]
        
        secilen_müdürlükler = st.multiselect("Müdürlükler", müdürlükler)
        
        kaynaklar = ["Beykoz Anlık", "Beykoz Burada", "Beykoz Duysun", "Diğer"]
        kaynak = st.selectbox("Kaynak", kaynaklar)
        
        sayi = st.number_input("Sayı", min_value=1, value=1)
        
        ayrinti = st.text_area("Ayrıntı", height=100)
        
        if st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True):
            if secilen_müdürlükler and ayrinti:
                yeni_kayitlar = []
                for mud in secilen_müdürlükler:
                    yeni_kayitlar.append({
                        "Tarih": tarih,
                        "Müdürlük": mud,
                        "Haber_Kaynagi": kaynak,
                        "Sayı": sayi,
                        "Ayrıntı": ayrinti,
                        "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                yeni_df = pd.DataFrame(yeni_kayitlar)
                df = pd.concat([df, yeni_df], ignore_index=True)
                
                kaydetme_tipi = veri_kaydet(df)
                
                if kaydetme_tipi == "google":
                    st.success(f"✅ {len(yeni_kayitlar)} kayıt Google Sheets'e eklendi!")
                else:
                    st.success(f"✅ {len(yeni_kayitlar)} kayıt local'e eklendi!")
                
                time.sleep(1)
                st.rerun()
            else:
                st.error("Lütfen müdürlük ve ayrıntı girin!")
    
    st.markdown("---")
    
    # VERİ YÖNETİMİ
    st.header("📁 Veri Yönetimi")
    
    # İndirme
    if not df.empty:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 CSV İndir",
            csv,
            f"beykoz_veriler_{date.today()}.csv",
            "text/csv",
            use_container_width=True
        )
    
    # Google Sheets durumu
    if PACKAGES_OK and "google" in st.secrets:
        st.markdown("---")
        if st.button("🔄 Google Sheets'e Senkronize Et", use_container_width=True):
            with st.spinner("Senkronize ediliyor..."):
                kaydetme_tipi = veri_kaydet(df)
                if kaydetme_tipi == "google":
                    st.success("✅ Senkronize edildi!")
                else:
                    st.error("❌ Senkronizasyon başarısız!")
            st.rerun()
    
    # Çıkış butonu
    st.markdown("---")
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.giris_yapildi = False
        st.rerun()

# ANA EKRAN
if not df.empty:
    # FİLTRELEME
    st.subheader("🔍 Filtrele")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bas_tarih = st.date_input("Başlangıç", value=date.today() - timedelta(days=30))
    
    with col2:
        bit_tarih = st.date_input("Bitiş", value=date.today())
    
    with col3:
        müdürlük_filtre = st.multiselect("Müdürlük", df['Müdürlük'].unique().tolist())
    
    # Filtre uygula
    mask = (df['Tarih'] >= bas_tarih) & (df['Tarih'] <= bit_tarih)
    
    if müdürlük_filtre:
        mask &= df['Müdürlük'].isin(müdürlük_filtre)
    
    filtrelenmis_df = df[mask].copy()
    
    # İSTATİSTİKLER
    st.markdown("---")
    
    ist1, ist2, ist3 = st.columns(3)
    
    with ist1:
        toplam_kayit = len(filtrelenmis_df)
        toplam_sayi = filtrelenmis_df['Sayı'].sum()
        st.metric("📊 Toplam", toplam_sayi, f"{toplam_kayit} kayıt")
    
    with ist2:
        müdürlük_sayisi = filtrelenmis_df['Müdürlük'].nunique()
        st.metric("🏢 Müdürlük", müdürlük_sayisi)
    
    with ist3:
        kaynak_sayisi = filtrelenmis_df['Haber_Kaynagi'].nunique()
        st.metric("📱 Kaynak", kaynak_sayisi)
    
    # TABLO
    st.markdown("---")
    st.subheader("📋 Kayıtlar")
    
    st.dataframe(
        filtrelenmis_df[['Tarih', 'Müdürlük', 'Haber_Kaynagi', 'Sayı', 'Ayrıntı']],
        use_container_width=True,
        hide_index=True
    )
    
    # EXCEL İNDİR
    st.markdown("---")
    
    if not filtrelenmis_df.empty:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            filtrelenmis_df.to_excel(writer, index=False, sheet_name='Rapor')
        
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            "📥 Excel Raporu İndir",
            excel_data,
            f"beykoz_rapor_{date.today().strftime('%Y%m%d')}.xlsx",
            "application/vnd.ms-excel",
            use_container_width=True
        )

else:
    # VERİ YOKSA
    st.info("""
    📭 **Henüz kayıt bulunmuyor.**
    
    İlk kaydınızı eklemek için:
    1. Sol taraftaki formu doldurun
    2. **💾 Kaydet** butonuna tıklayın
    """)

# ALT BİLGİ
st.markdown("---")
st.caption(f"© 2026 MAB tarafından geliştirildi. • Kullanıcı: {st.session_state.isim} • Kayıt: {len(df)}")
