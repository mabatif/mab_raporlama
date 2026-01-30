import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io
import json
import base64
import os

# ===== RAILWAY OPTIMIZATION =====
# Railway'de stable çalışması için
st.set_page_config(
    page_title="Beykoz Haber Takip",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://t.me/beykozdestek',
        'Report a bug': None,
        'About': "Beykoz Belediyesi Haber Takip Sistemi v1.0"
    }
)

# ===== VERİTABANI SİSTEMİ (Railway için) =====
class RailwayDatabase:
    """Railway'de çalışan veritabanı"""
    
    def __init__(self):
        # Railway environment variable kullan
        self.db_file = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/data/beykoz_db.json")
        self.ensure_directory()
    
    def ensure_directory(self):
        """Dizin yoksa oluştur"""
        directory = os.path.dirname(self.db_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def load(self):
        """Verileri yükle"""
        try:
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                df = pd.DataFrame(data)
                
                # Tarih formatını düzelt
                if 'Tarih' in df.columns and not df.empty:
                    df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
                
                return df
            else:
                return self._create_empty()
                
        except Exception as e:
            st.error(f"Veri yükleme hatası: {e}")
            return self._create_empty()
    
    def save(self, df):
        """Verileri kaydet"""
        try:
            # DataFrame'i temizle
            df_copy = df.copy()
            
            # Tarih sütununu string yap
            if 'Tarih' in df_copy.columns:
                df_copy['Tarih'] = df_copy['Tarih'].astype(str)
            
            # NaN değerleri temizle
            df_copy = df_copy.fillna('')
            
            # JSON'a çevir ve kaydet
            data = df_copy.to_dict(orient='records')
            
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            st.error(f"Kaydetme hatası: {e}")
            return False
    
    def _create_empty(self):
        """Boş DataFrame oluştur"""
        columns = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
        return pd.DataFrame(columns=columns)
    
    def add_record(self, tarih, mudurlukler, kaynak, sayi, ayrinti):
        """Yeni kayıt ekle"""
        df = self.load()
        
        new_records = []
        for mudurluk in mudurlukler:
            new_records.append({
                "Tarih": tarih,
                "Müdürlük": mudurluk,
                "Haber_Kaynagi": kaynak,
                "Sayı": sayi,
                "Ayrıntı": ayrinti,
                "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        new_df = pd.DataFrame(new_records)
        df = pd.concat([df, new_df], ignore_index=True)
        
        return self.save(df), len(new_records)

# ===== GÜVENLİK SİSTEMİ =====
def railway_auth():
    """Railway için güvenlik"""
    
    if 'rw_logged_in' not in st.session_state:
        st.session_state.rw_logged_in = False
        st.session_state.rw_user = None
        st.session_state.rw_role = None
    
    if not st.session_state.rw_logged_in:
        # GİRİŞ EKRANI
        st.markdown("""
        <style>
        .railway-login {
            max-width: 500px;
            margin: 50px auto;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            color: white;
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="railway-login">', unsafe_allow_html=True)
        st.markdown('<h1>🔐 BEYKOZ SİSTEMİ</h1>', unsafe_allow_html=True)
        st.markdown('<p>Railway.app üzerinde</p>', unsafe_allow_html=True)
        
        # Kullanıcı bilgileri
        username = st.text_input("Kullanıcı Adı", key="rw_user_input")
        password = st.text_input("Şifre", type="password", key="rw_pass_input")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 GİRİŞ YAP", type="primary", use_container_width=True):
                # Basit kullanıcı kontrolü
                users = {
                    "admin": {"pass": "Beykoz2024!", "role": "admin", "name": "Yönetici"},
                    "editor": {"pass": "Edit123!", "role": "editor", "name": "Editör"},
                    "viewer": {"pass": "View456!", "role": "viewer", "name": "Görüntüleyici"}
                }
                
                if username in users and password == users[username]["pass"]:
                    st.session_state.rw_logged_in = True
                    st.session_state.rw_user = username
                    st.session_state.rw_role = users[username]["role"]
                    st.session_state.rw_name = users[username]["name"]
                    st.success("Giriş başarılı!")
                    st.rerun()
                else:
                    st.error("Hatalı giriş!")
        
        st.markdown("""
        <br>
        <p><strong>Demo Kullanıcılar:</strong></p>
        <p>• admin / Beykoz2024!</p>
        <p>• editor / Edit123!</p>
        <p>• viewer / View456!</p>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()
    
    return True

# ===== GİRİŞ KONTROLÜ =====
railway_auth()

# ===== VERİTABANI BAŞLAT =====
db = RailwayDatabase()

# ===== SİSTEM AYARLARI =====
MUDURLUKLER = [
    "Fen İşleri Müdürlüğü",
    "Temizlik İşleri Müdürlüğü", 
    "Zabıta Müdürlüğü",
    "İşletme ve İştirakler Müdürlüğü",
    "Özel Kalem Müdürlüğü",
    "Kültür ve Sosyal İşler Müdürlüğü",
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
    "Diğer"
]

HABER_KAYNAKLARI = [
    "Beykoz Anlık", 
    "Beykoz Burada", 
    "Beykoz Duysun", 
    "Beykoz Güncel", 
    "Diğer"
]

# ===== ANA UYGULAMA =====
st.title("📊 BEYKOZ HABER TAKİP SİSTEMİ")
st.markdown(f"**🚂 Railway.app** • Kullanıcı: {st.session_state.rw_name} ({st.session_state.rw_role})")
st.markdown("---")

# Verileri yükle
with st.spinner("Veritabanı yükleniyor..."):
    df = db.load()

if df.empty:
    st.info("📭 Henüz kayıt yok. İlk kaydınızı ekleyin!")
else:
    st.success(f"✅ {len(df)} kayıt yüklendi!")

# ===== SİDEBAR =====
with st.sidebar:
    st.header("📝 Yeni Kayıt")
    
    with st.form("railway_new", border=True):
        tarih = st.date_input("📅 Tarih", value=date.today(), format="DD/MM/YYYY")
        
        secilen_mudurlukler = st.multiselect(
            "🏢 Müdürlükler", 
            MUDURLUKLER, 
            placeholder="Seçiniz...",
            max_selections=5
        )
        
        kaynak = st.selectbox("📱 Kaynak", HABER_KAYNAKLARI)
        
        if kaynak == "Diğer":
            diger_kaynak = st.text_input("✏️ Kaynak Adı", placeholder="Yazın...")
            if diger_kaynak:
                kaynak = diger_kaynak
        
        sayi = st.number_input("🔢 Sayı", min_value=1, value=1)
        
        ayrinti = st.text_area("📝 Ayrıntı", height=120, placeholder="Detaylı açıklama...")
        
        if st.form_submit_button("💾 KAYDET", type="primary", use_container_width=True):
            if not secilen_mudurlukler:
                st.error("❌ Lütfen en az bir müdürlük seçin!")
            elif not ayrinti.strip():
                st.error("❌ Lütfen ayrıntı girin!")
            else:
                success, count = db.add_record(tarih, secilen_mudurlukler, kaynak, sayi, ayrinti)
                if success:
                    st.success(f"✅ {count} kayıt eklendi!")
                    st.rerun()
                else:
                    st.error("❌ Kayıt eklenemedi!")
    
    st.markdown("---")
    
    # VERİ YÖNETİMİ
    st.header("📁 Veri Yönetimi")
    
    # CSV İndir
    if not df.empty:
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 CSV İndir",
            csv,
            f"beykoz_railyway_{date.today()}.csv",
            "text/csv",
            use_container_width=True
        )
    
    # VERİ YÜKLE
    st.markdown("---")
    st.subheader("📤 CSV Yükle")
    
    uploaded_file = st.file_uploader("CSV dosyası seç", type=['csv'])
    if uploaded_file is not None:
        try:
            yeni_df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
            
            # Kolon kontrolü
            required = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı"]
            if all(col in yeni_df.columns for col in required):
                # Mevcut verilerle birleştir
                df = pd.concat([df, yeni_df], ignore_index=True)
                
                if db.save(df):
                    st.success(f"✅ {len(yeni_df)} kayıt yüklendi!")
                    st.rerun()
                else:
                    st.error("❌ Yükleme başarısız!")
            else:
                st.error("❌ CSV formatı uygun değil!")
                
        except Exception as e:
            st.error(f"❌ Hata: {e}")
    
    # YÖNETİCİ ARAÇLARI
    if st.session_state.rw_role == "admin":
        st.markdown("---")
        st.subheader("⚠️ Yönetici")
        
        if st.button("🗑️ Verileri Temizle", type="secondary", use_container_width=True):
            if st.checkbox("EMİN MİSİNİZ? Tüm veriler silinecek!"):
                bos_df = pd.DataFrame(columns=["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"])
                if db.save(bos_df):
                    st.success("✅ Veriler temizlendi!")
                    st.rerun()
    
    # ÇIKIŞ
    st.markdown("---")
    if st.button("🚪 Çıkış Yap", type="secondary", use_container_width=True):
        st.session_state.rw_logged_in = False
        st.rerun()

# ===== ANA SAYFA =====
if not df.empty:
    # FİLTRELEME
    st.subheader("🔍 Filtrele")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bas_tarih = st.date_input("Başlangıç", 
                                 value=date.today() - timedelta(days=30),
                                 key="bas_tarih_railway")
    
    with col2:
        bit_tarih = st.date_input("Bitiş", 
                                 value=date.today(),
                                 key="bit_tarih_railway")
    
    with col3:
        filt_mud = st.multiselect("Müdürlük", 
                                 MUDURLUKLER,
                                 placeholder="Tümü",
                                 key="filt_mud_railway")
    
    with col4:
        filt_kaynak = st.multiselect("Kaynak",
                                    HABER_KAYNAKLARI,
                                    placeholder="Tümü",
                                    key="filt_kaynak_railway")
    
    # Filtre uygula
    if not df.empty and 'Tarih' in df.columns:
        try:
            mask = (df['Tarih'] >= bas_tarih) & (df['Tarih'] <= bit_tarih)
            
            if filt_mud:
                mask &= df['Müdürlük'].isin(filt_mud)
            
            if filt_kaynak:
                mask &= df['Haber_Kaynagi'].isin(filt_kaynak)
            
            filtrelenmis_df = df[mask].copy()
            
        except Exception as e:
            st.error(f"Filtreleme hatası: {e}")
            filtrelenmis_df = df.copy()
    else:
        filtrelenmis_df = df.copy()
    
    # İSTATİSTİKLER
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
    
    # TABLO
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
    
    # Değişiklikleri kaydet
    if st.button("💾 Değişiklikleri Kaydet", type="primary", use_container_width=True):
        # Orijinal df'yi güncelle
        for idx in filtrelenmis_df.index:
            if idx < len(duzenlenen_df):
                df.loc[idx, 'Tarih'] = duzenlenen_df.iloc[idx]['Tarih']
                df.loc[idx, 'Müdürlük'] = duzenlenen_df.iloc[idx]['Müdürlük']
                df.loc[idx, 'Haber_Kaynagi'] = duzenlenen_df.iloc[idx]['Haber_Kaynagi']
                df.loc[idx, 'Sayı'] = duzenlenen_df.iloc[idx]['Sayı']
                df.loc[idx, 'Ayrıntı'] = duzenlenen_df.iloc[idx]['Ayrıntı']
        
        # Kaydet
        if db.save(df):
            st.success("✅ Değişiklikler kaydedildi!")
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
            filtrelenmis_df.to_excel(writer, index=False, sheet_name='Rapor')
            
            workbook = writer.book
            worksheet = writer.sheets['Rapor']
            
            # Format
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#2c3e50',
                'font_color': 'white',
                'border': 1
            })
            
            # Sütun genişlikleri
            worksheet.set_column('A:A', 12)
            worksheet.set_column('B:B', 25)
            worksheet.set_column('C:C', 20)
            worksheet.set_column('D:D', 10)
            worksheet.set_column('E:E', 50)
            worksheet.set_column('F:F', 20)
            
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

else:
    # VERİ YOKSA
    st.info("""
    📭 **Henüz kayıt bulunmuyor.**
    
    İlk kaydınızı eklemek için:
    1. Sol taraftaki formu doldurun
    2. **💾 KAYDET** butonuna tıklayın
    """)
    
    # Örnek veri butonu
    if st.button("🚀 Örnek Veri Oluştur"):
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
        df = pd.concat([df, ornek_df], ignore_index=True)
        
        if db.save(df):
            st.success("✅ Örnek veriler eklendi!")
            st.rerun()

# ===== FOOTER =====
st.markdown("---")
st.caption(f"© 2026 MAB ile geliştirildi. • Railway.app • {datetime.now().strftime('%H:%M:%S')}")
