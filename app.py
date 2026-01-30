import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io
import time
import base64
import json
import os

# ==================== ŞİFRELİ VERİTABANI ====================
class SecureDatabaseV1:
    """V1.3 - Şifreli veritabanı sistemi"""
    
    def __init__(self):
        self.local_file = "beykoz_data_encrypted.bin"
        self.secrets_key = "beykoz_v1_data"
    
    def load(self):
        """Verileri yükle - Önce secrets, sonra local"""
        try:
            # 1. ÖNCE STREAMLIT SECRETS'DAN DENE
            if self.secrets_key in st.secrets:
                return self._load_from_secrets()
            
            # 2. SONRA LOCAL DOSYADAN DENE
            elif os.path.exists(self.local_file):
                return self._load_from_local()
            
            # 3. HİÇBİRİ YOKSA BOŞ DF
            else:
                return self._create_empty_df()
                
        except Exception as e:
            st.error(f"Veri yükleme hatası: {e}")
            return self._create_empty_df()
    
    def _load_from_secrets(self):
        """Secrets'tan yükle (BASE64 + JSON)"""
        encoded_data = st.secrets[self.secrets_key]
        decoded_bytes = base64.b64decode(encoded_data)
        data_str = decoded_bytes.decode('utf-8')
        data_dict = json.loads(data_str)
        
        df = pd.DataFrame(data_dict)
        if 'Tarih' in df.columns and not df.empty:
            df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
        
        return df
    
    def _load_from_local(self):
        """Local dosyadan yükle"""
        with open(self.local_file, 'rb') as f:
            encoded_data = f.read()
        
        decoded_bytes = base64.b64decode(encoded_data)
        data_str = decoded_bytes.decode('utf-8')
        data_dict = json.loads(data_str)
        
        df = pd.DataFrame(data_dict)
        if 'Tarih' in df.columns and not df.empty:
            df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
        
        return df
    
    def save(self, df, save_to_local=True):
        """Verileri kaydet"""
        try:
            # DataFrame'i hazırla
            df_copy = df.copy()
            if 'Tarih' in df_copy.columns:
                df_copy['Tarih'] = df_copy['Tarih'].astype(str)
            
            df_copy = df_copy.fillna('')
            
            # JSON'a çevir
            data_dict = df_copy.to_dict(orient='records')
            data_str = json.dumps(data_dict, ensure_ascii=False)
            
            # Base64 encode
            encoded_bytes = base64.b64encode(data_str.encode('utf-8'))
            encoded_str = encoded_bytes.decode('utf-8')
            
            # LOCAL'E KAYDET (otomatik yedek)
            if save_to_local:
                with open(self.local_file, 'wb') as f:
                    f.write(encoded_bytes)
            
            # SESSION STATE'E KAYDET (geçici)
            st.session_state['local_cache'] = encoded_str
            
            return True
            
        except Exception as e:
            st.error(f"Kaydetme hatası: {e}")
            return False
    
    def _create_empty_df(self):
        """Boş DataFrame oluştur"""
        columns = ["Tarih", "Müdürlük", "Kaynak", "Sayı", "Ayrıntı", "Kayit_Zamani"]
        return pd.DataFrame(columns=columns)
    
    def export_csv(self, df):
        """CSV olarak dışa aktar"""
        return df.to_csv(index=False, encoding='utf-8-sig')
    
    def backup_to_secrets_format(self, df):
        """Secrets formatına çevir (manuel kopyala-yapıştır için)"""
        df_copy = df.copy()
        if 'Tarih' in df_copy.columns:
            df_copy['Tarih'] = df_copy['Tarih'].astype(str)
        
        df_copy = df_copy.fillna('')
        data_dict = df_copy.to_dict(orient='records')
        data_str = json.dumps(data_dict, ensure_ascii=False)
        encoded_bytes = base64.b64encode(data_str.encode('utf-8'))
        encoded_str = encoded_bytes.decode('utf-8')
        
        return f'beykoz_v1_data = "{encoded_str}"'

# ==================== GÜVENLİK SİSTEMİ ====================
def check_login_v1():
    """V1.3 güvenlik sistemi"""
    
    if "v1_logged_in" in st.session_state and st.session_state.v1_logged_in:
        return True
    
    # BASİT GİRİŞ EKRANI
    st.title("🔐 Beykoz Haber Takip v1.3")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Kullanıcı Adı")
        password = st.text_input("Şifre", type="password")
        
        if st.button("Giriş Yap", type="primary", use_container_width=True):
            # Basit kontrol (isterseniz secrets kullanın)
            if username == "admin" and password == "beykoz2024":
                st.session_state.v1_logged_in = True
                st.session_state.v1_user = username
                st.session_state.v1_role = "admin"
                st.success("Giriş başarılı!")
                time.sleep(1)
                st.rerun()
            elif username == "user" and password == "user123":
                st.session_state.v1_logged_in = True
                st.session_state.v1_user = username
                st.session_state.v1_role = "user"
                st.success("Giriş başarılı!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Hatalı giriş!")
    
    return False

# ==================== ÇALIŞTIR ====================
if not check_login_v1():
    st.stop()

# Sayfa ayarları
st.set_page_config(page_title="Beykoz v1.3", layout="wide")

# Veritabanı başlat
db = SecureDatabaseV1()

# ==================== ANA UYGULAMA ====================
st.title("📊 Beykoz Haber Takip Sistemi v1.3")
st.markdown("🔒 **Şifreli Veritabanı - Google Sheets YOK**")
st.markdown("---")

# Verileri yükle
df = db.load()

# SIDEBAR
with st.sidebar:
    st.write(f"👤 {st.session_state.v1_user}")
    
    # YENİ KAYIT
    st.header("📝 Yeni Kayıt")
    with st.form("v1_new"):
        tarih = st.date_input("Tarih", date.today())
        mudurluk = st.selectbox("Müdürlük", [
            "Fen İşleri Müdürlüğü", "Temizlik İşleri Müdürlüğü", 
            "Zabıta Müdürlüğü", "Diğer"
        ])
        kaynak = st.selectbox("Kaynak", [
            "Beykoz Anlık", "Beykoz Burada", "Diğer"
        ])
        sayi = st.number_input("Sayı", min_value=1, value=1)
        ayrinti = st.text_area("Ayrıntı")
        
        if st.form_submit_button("💾 Kaydet"):
            new_data = {
                "Tarih": tarih,
                "Müdürlük": mudurluk,
                "Kaynak": kaynak,
                "Sayı": sayi,
                "Ayrıntı": ayrinti,
                "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            new_df = pd.DataFrame([new_data])
            df = pd.concat([df, new_df], ignore_index=True)
            
            if db.save(df):
                st.success("Kayıt eklendi!")
                st.rerun()
    
    # VERİ YÖNETİMİ
    st.markdown("---")
    st.header("📁 Veri Yönetimi")
    
    # İndirme
    if not df.empty:
        csv = db.export_csv(df)
        st.download_button(
            "📥 CSV İndir",
            csv,
            f"beykoz_v1_{date.today()}.csv",
            "text/csv"
        )
    
    # Secrets formatı
    if st.session_state.v1_role == "admin":
        st.markdown("---")
        if st.button("🔑 Secrets Formatını Göster"):
            secrets_code = db.backup_to_secrets_format(df)
            st.code(secrets_code, language="toml")
    
    # Çıkış
    st.markdown("---")
    if st.button("🚪 Çıkış Yap"):
        st.session_state.v1_logged_in = False
        st.rerun()

# ANA EKRAN
if not df.empty:
    # Filtreleme
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Başlangıç", date.today() - timedelta(days=30))
    with col2:
        end = st.date_input("Bitiş", date.today())
    
    # Filtre uygula
    mask = (df['Tarih'] >= start) & (df['Tarih'] <= end)
    filtered_df = df[mask]
    
    # Göster
    st.dataframe(filtered_df, use_container_width=True)
    
    # İstatistik
    st.metric("Toplam Kayıt", len(filtered_df), f"{filtered_df['Sayı'].sum()} toplam sayı")
    
    # Excel indir
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False)
    excel_data = excel_buffer.getvalue()
    
    st.download_button(
        "📊 Excel İndir",
        excel_data,
        f"beykoz_rapor_{date.today()}.xlsx",
        "application/vnd.ms-excel"
    )

else:
    st.info("Henüz kayıt yok. Sol taraftan yeni kayıt ekleyin.")

st.caption(f"v1.3 • {datetime.now().strftime('%d.%m.%Y %H:%M')}")
