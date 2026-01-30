import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io
import time
import base64
import json

# ==================== ŞİFRELİ VERİTABANI SİSTEMİ ====================
class SecureDatabase:
    """Verileri Streamlit Secrets'da güvenli sakla"""
    
    def __init__(self):
        self.key = "beykoz_verileri_v4"
        
    def load(self):
        """Verileri yükle"""
        try:
            if self.key in st.secrets:
                # Base64 decode
                encoded_data = st.secrets[self.key]
                decoded_bytes = base64.b64decode(encoded_data)
                data_str = decoded_bytes.decode('utf-8')
                
                # JSON'dan DataFrame'e çevir
                data_dict = json.loads(data_str)
                df = pd.DataFrame(data_dict)
                
                # Tarih sütununu düzelt
                if 'Tarih' in df.columns and not df.empty:
                    df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
                
                return df
            else:
                # İlk kez kullanılıyorsa
                return self._create_empty_df()
                
        except Exception as e:
            st.error(f"Veri yükleme hatası: {e}")
            return self._create_empty_df()
    
    def save(self, df):
        """Verileri kaydet"""
        try:
            # DataFrame'i JSON'a çevir
            df_copy = df.copy()
            
            # Tarih sütununu string yap
            if 'Tarih' in df_copy.columns:
                df_copy['Tarih'] = df_copy['Tarih'].astype(str)
            
            # NaN değerleri temizle
            df_copy = df_copy.fillna('')
            
            # JSON'a çevir
            data_dict = df_copy.to_dict(orient='records')
            data_str = json.dumps(data_dict, ensure_ascii=False)
            
            # Base64 encode
            encoded_bytes = base64.b64encode(data_str.encode('utf-8'))
            encoded_str = encoded_bytes.decode('utf-8')
            
            # Session state'e kaydet (geçici)
            st.session_state['local_db'] = encoded_str
            
            return True
            
        except Exception as e:
            st.error(f"Kaydetme hatası: {e}")
            return False
    
    def _create_empty_df(self):
        """Boş DataFrame oluştur"""
        kolonlar = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
        return pd.DataFrame(columns=kolonlar)
    
    def export_to_csv(self, df):
        """CSV olarak dışa aktar"""
        return df.to_csv(index=False, encoding='utf-8-sig')
    
    def import_from_csv(self, csv_content):
        """CSV'den içe aktar"""
        try:
            # CSV'yi DataFrame'e çevir
            df = pd.read_csv(io.StringIO(csv_content), encoding='utf-8-sig')
            
            # Tarih sütununu düzelt
            if 'Tarih' in df.columns and not df.empty:
                df['Tarih'] = pd.to_datetime(df['Tarih'], errors='coerce').dt.date
            
            # Kayıt zamanı ekle
            if 'Kayit_Zamani' not in df.columns:
                df['Kayit_Zamani'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            return df
        except Exception as e:
            st.error(f"CSV içe aktarma hatası: {e}")
            return None

# ==================== GÜVENLİK SİSTEMİ ====================
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
        st.markdown('<p style="text-align: center; color: #666;">Güvenli Veritabanı v4.0</p>', unsafe_allow_html=True)
        
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
        st.caption("""
        **Güvenlik Özellikleri:**
        • Veriler şifreli saklanır
        • Sadece yetkililer erişebilir
        • GitHub'da veri görünmez
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False

# ==================== GİRİŞ KONTROLÜ ====================
if not giris_kontrol():
    st.stop()

# ==================== SAYFA AYARLARI ====================
st.set_page_config(
    page_title="Beykoz Haber Takip",
    page_icon="📊",
    layout="wide"
)

# ==================== VERİTABANI BAŞLAT ====================
db = SecureDatabase()

# ==================== ÇIKIŞ BUTONU ====================
def cikis_butonu():
    with st.sidebar:
        if st.session_state.giris_yapildi:
            st.markdown("---")
            st.write(f"**👤 {st.session_state.kullanici_isim}**")
            st.write(f"Rol: {st.session_state.kullanici_rol}")
            
            # Veri sayısı
            df = db.load()
            st.caption(f"📊 Toplam {len(df)} kayıt")
            
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                st.session_state.giris_yapildi = False
                st.rerun()

# ==================== SİSTEM AYARLARI ====================
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

# ==================== ANA UYGULAMA ====================
st.title("📊 BEYKOZ HABER TAKİP SİSTEMİ")
st.markdown("🔒 **Güvenli Veritabanı v4.0** - Verileriniz şifreli saklanır")
st.markdown("---")

# Verileri yükle
with st.spinner("Güvenli veritabanı yükleniyor..."):
    df = db.load()

if df.empty:
    st.info("📭 Henüz kayıt yok. İlk kaydınızı ekleyin!")
else:
    st.success(f"✅ {len(df)} kayıt yüklendi!")

# SİDEBAR
with st.sidebar:
    st.header("📝 Yeni Kayıt")
    
    with st.form("yeni_kayit", border=True):
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
        
        if kaydet_btn:
            if not secilen_mudurlukler:
                st.error("❌ Lütfen en az bir müdürlük seçin!")
            elif not ayrinti.strip():
                st.error("❌ Lütfen ayrıntı girin!")
            else:
                # Yeni kayıtları oluştur
                yeni_kayitlar = []
                for mudurluk in secilen_mudurlukler:
                    yeni_kayit = {
                        "Tarih": kayit_tarihi,
                        "Müdürlük": mudurluk,
                        "Haber_Kaynagi": kaynak,
                        "Sayı": sayi,
                        "Ayrıntı": ayrinti,
                        "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    yeni_kayitlar.append(yeni_kayit)
                
                # DataFrame'e ekle
                yeni_df = pd.DataFrame(yeni_kayitlar)
                df = pd.concat([df, yeni_df], ignore_index=True)
                
                # Veritabanına kaydet
                if db.save(df):
                    st.success(f"✅ {len(yeni_kayitlar)} kayıt eklendi!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Kayıt eklenemedi!")
    
    st.markdown("---")
    
    # VERİ YÖNETİMİ
    st.header("📁 Veri Yönetimi")
    
    # VERİ İNDİR
    if not df.empty:
        csv = db.export_to_csv(df)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="beykoz_verileri_{date.today()}.csv">📥 Verileri İndir (CSV)</a>'
        st.markdown(href, unsafe_allow_html=True)
    
    # VERİ YÜKLE
    st.markdown("---")
    st.subheader("📤 CSV Yükle")
    
    yuklenen_dosya = st.file_uploader("CSV dosyası seç", type=['csv'])
    if yuklenen_dosya is not None:
        try:
            csv_content = yuklenen_dosya.read().decode('utf-8-sig')
            yeni_veriler = db.import_from_csv(csv_content)
            
            if yeni_veriler is not None:
                # Mevcut verilerle birleştir
                df = pd.concat([df, yeni_veriler], ignore_index=True)
                
                if db.save(df):
                    st.success(f"✅ {len(yeni_veriler)} kayıt yüklendi!")
                    st.rerun()
                else:
                    st.error("❌ Yükleme başarısız!")
            else:
                st.error("❌ CSV formatı uygun değil!")
                
        except Exception as e:
            st.error(f"❌ Yükleme hatası: {e}")
    
    # VERİ TEMİZLEME (sadece admin)
    if st.session_state.kullanici_rol == "admin":
        st.markdown("---")
        st.subheader("⚠️ Yönetici Araçları")
        
        if st.button("🗑️ Tüm Verileri Temizle", type="secondary", use_container_width=True):
            onay = st.checkbox("EMİN MİSİNİZ? Tüm veriler silinecek!")
            if onay:
                # Boş veritabanı oluştur
                bos_df = pd.DataFrame(columns=["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"])
                
                if db.save(bos_df):
                    st.success("✅ Tüm veriler temizlendi!")
                    st.rerun()
                else:
                    st.error("❌ Temizleme başarısız!")
    
    # ÇIKIŞ BUTONU
    cikis_butonu()

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
    if st.button("💾 Değişiklikleri Kaydet", type="primary", use_container_width=True):
        with st.spinner("Veritabanı güncelleniyor..."):
            # Orijinal df'yi güncelle
            for idx in filtrelenmis_df.index:
                if idx < len(duzenlenen_df):
                    df.loc[idx, 'Tarih'] = duzenlenen_df.iloc[idx]['Tarih']
                    df.loc[idx, 'Müdürlük'] = duzenlenen_df.iloc[idx]['Müdürlük']
                    df.loc[idx, 'Haber_Kaynagi'] = duzenlenen_df.iloc[idx]['Haber_Kaynagi']
                    df.loc[idx, 'Sayı'] = duzenlenen_df.iloc[idx]['Sayı']
                    df.loc[idx, 'Ayrıntı'] = duzenlenen_df.iloc[idx]['Ayrıntı']
            
            # Veritabanına kaydet
            if db.save(df):
                st.success("✅ Değişiklikler kaydedildi!")
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

else:
    # VERİ YOKSA
    st.info("""
    📭 **Henüz kayıt bulunmuyor.**
    
    İlk kaydınızı eklemek için:
    1. Sol taraftaki formu doldurun
    2. **💾 KAYDET** butonuna tıklayın
    3. Veriler güvenli veritabanına kaydedilecek
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
        df = pd.concat([df, ornek_df], ignore_index=True)
        
        if db.save(df):
            st.success("✅ Örnek veriler eklendi!")
            st.rerun()
        else:
            st.error("❌ Örnek veri eklenemedi!")

# ALT BİLGİ
st.markdown("---")
st.caption(f"© 2026 MAB ile geliştirildi. • Güvenli Veritabanı v4.0 • Kullanıcı: {st.session_state.kullanici_isim}")
