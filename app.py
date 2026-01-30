# ==== 1. GÜVENLİK VE TEMEL AYARLAR ====
import streamlit as st
import os
import pandas as pd
from datetime import date, datetime
import io

# FPDF için DOĞRU import
try:
    from fpdf import FPDF
except ImportError:
    st.error("fpdf2 paketi yüklü değil. Lütfen 'gereksinimler.txt' dosyasını kontrol edin.")
    st.stop()

# ==== 2. GÜVENLİ VERİTABANI YOLU ====
# Veritabanı gizli klasörde saklanacak
DATA_DIR = ".data"
DOSYA_ADI = os.path.join(DATA_DIR, 'beykoz_veritabani_v2.csv')

# Klasör yoksa oluştur
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==== 3. ŞİFRE KONTROL FONKSİYONU ====
def sifre_kontrol():
    """Kullanıcı giriş kontrolü"""
    
    # Eğer zaten giriş yapılmışsa devam et
    if "giris_yapildi" in st.session_state and st.session_state.giris_yapildi:
        return True
    
    # GİRİŞ EKRANI
    st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        st.markdown("<h2 style='text-align: center;'>🔐 Beykoz Sistemi</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>Güvenli Giriş</p>", unsafe_allow_html=True)
        
        kullanici = st.text_input("**Kullanıcı Adı**", placeholder="admin")
        sifre = st.text_input("**Şifre**", type="password", placeholder="••••••••")
        
        if st.button("**Giriş Yap**", type="primary", use_container_width=True):
            if kullanici in st.secrets["users"]:
                kullanici_bilgisi = st.secrets["users"][kullanici]
                
                if sifre == kullanici_bilgisi["password"]:
                    st.session_state.giris_yapildi = True
                    st.session_state.kullanici_adi = kullanici
                    st.session_state.kullanici_rol = kullanici_bilgisi["role"]
                    st.session_state.kullanici_isim = kullanici_bilgisi["name"]
                    
                    st.success(f"✅ Hoş geldiniz, {kullanici_bilgisi['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Hatalı şifre!")
            else:
                st.error("❌ Kullanıcı bulunamadı!")
        
        st.markdown("---")
        st.caption("""
        **Test Kullanıcıları:**
        - admin / admin123
        - editor / edit123
        - viewer / view123
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False

# ==== 4. GİRİŞ KONTROLÜ ====
if not sifre_kontrol():
    st.stop()

# ==== 5. SAYFA AYARLARI ====
st.set_page_config(
    page_title="Beykoz Haber Rapor",
    page_icon="📊",
    layout="wide"
)

# ==== 6. ÇIKIŞ BUTONU ====
def cikis_butonu():
    with st.sidebar:
        if st.session_state.giris_yapildi:
            st.markdown("---")
            st.write(f"**👤 {st.session_state.kullanici_isim}**")
            st.write(f"*({st.session_state.kullanici_rol})*")
            
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                st.session_state.giris_yapildi = False
                st.rerun()

# ==== 7. SİZİN ORİJİNAL KODUNUZ (DÜZENLENMİŞ) ====
# --- AYARLAR ---
# DOSYA_ADI zaten yukarıda tanımlandı

# V1.2 - GÜNCELLENMİŞ MÜDÜRLÜK LİSTESİ
MUDURLUKLER = [
    "Fen İşleri Müdürlüğü",
    "Temizlik İşleri Müdürlüğü", 
    "Zabıta Müdürlüğü",
    "İşletme ve İştirakler Müdürlüğü",
    "Özel Kalem Müdürlüğü",
    "Kültür ve Sosyal İşler Müdürlüğü",
    # ... diğer müdürlükler (orijinal listeniz)
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
if 'diger_kaynak' not in st.session_state:
    st.session_state.diger_kaynak = ""

# --- YARDIMCI FONKSİYONLAR ---
def tarih_formatla(tarih_obj):
    if isinstance(tarih_obj, str):
        try:
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

def kaydet_ve_sifirla():
    secilen_mudurlukler = st.session_state.form_mudurlukler
    if not secilen_mudurlukler:
        st.error("Lütfen en az bir müdürlük seçiniz!")
        return False
    
    kaynak = st.session_state.form_kaynak
    if kaynak == "Diğer":
        diger_kaynak = st.session_state.diger_kaynak.strip()
        if not diger_kaynak:
            st.error("Lütfen 'Diğer' kaynak için açıklama giriniz!")
            return False
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
    st.session_state.diger_kaynak = ""
    return True

# ==== 8. ARAYÜZ ====
st.title("📊 Beykoz Haber Hesapları - Yönetici Paneli")
st.caption("V1.3 - Güvenli Sistem")

# --- SOL MENÜ: VERİ GİRİŞİ ---
with st.sidebar:
    st.header("📝 Veri Girişi")
    with st.form("giris_formu", clear_on_submit=False):
        st.date_input("Tarih", value=date.today(), format="DD/MM/YYYY", key="form_tarih")
        
        st.multiselect(
            "Müdürlükler",
            MUDURLUKLER,
            key="form_mudurlukler",
            placeholder="Müdürlük seçiniz..."
        )
        
        kaynak_secim = st.selectbox("Kaynak", HABER_KAYNAKLARI, key="form_kaynak")
        
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
    try:
        df['Tarih'] = pd.to_datetime(df['Tarih']).dt.date
    except:
        pass

# FİLTRELER
st.markdown("### 🔍 Rapor Filtreleme")
c1, c2, c3, c4 = st.columns(4)
bas = c1.date_input("Başlangıç Tarihi", date.today(), format="DD/MM/YYYY")
bit = c2.date_input("Bitiş Tarihi", date.today(), format="DD/MM/YYYY")
mud_sec = c3.multiselect("Müdürlük Filtresi", MUDURLUKLER, placeholder="Tüm müdürlükler")
kaynak_sec = c4.multiselect("Kaynak Filtresi", HABER_KAYNAKLARI, placeholder="Tüm kaynaklar")

# ... ORİJİNAL KODUNUZUN KALANI BURAYA GELECEK ...
# (Veri işleme, tablolar, PDF oluşturma vs.)

# ==== 9. ÇIKIŞ BUTONUNU ÇAĞIR ====
cikis_butonu()

# ==== 10. BAŞLANGIÇ MESAJI ====
if not os.path.exists(DOSYA_ADI):
    st.info("📁 İlk kez kullanıyorsunuz. Veritabanı otomatik oluşturuldu.")
