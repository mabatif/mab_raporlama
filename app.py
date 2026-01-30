import streamlit as st
import os
import pandas as pd
from datetime import date, datetime, timedelta
import io
import time


# ==== 2. GÜVENLİ VERİTABANI YOLU ====
# Veriler gizli klasörde saklanacak
DATA_DIR = ".data"
DOSYA_ADI = os.path.join(DATA_DIR, 'beykoz_haber_veritabani.csv')

# Klasör yoksa oluştur
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==== 3. ŞİFRE KONTROL SİSTEMİ ====
def giris_kontrol():
    """Güvenli kullanıcı girişi"""
    
    # Eğer giriş yapılmışsa devam et
    if "giris_yapildi" in st.session_state and st.session_state.giris_yapildi:
        return True
    
    # GİRİŞ EKRANI TASARIMI
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
    .login-title {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 30px;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 10px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Giriş formu
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown('<h2 class="login-title">🔐 HABER TAKİP RAPOR SİSTEMİ </h2>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #666; margin-bottom: 30px;">Güvenli Giriş Paneli</p>', unsafe_allow_html=True)
        
        kullanici = st.text_input("**Kullanıcı Adı**", placeholder="admin")
        sifre = st.text_input("**Şifre**", type="password", placeholder="••••••••")
        
        if st.button("**GİRİŞ YAP**", type="primary", use_container_width=True):
            if "users" in st.secrets and kullanici in st.secrets["users"]:
                kullanici_bilgisi = st.secrets["users"][kullanici]
                
                if sifre == kullanici_bilgisi["password"]:
                    # Giriş başarılı
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
        
        # Bilgilendirme
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 14px;">
        <p><strong>📞 Yardım için:</strong> Sistem Yöneticisi</p>
        <p>🔒 Verileriniz güvende</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False

# ==== 4. GİRİŞ KONTROLÜNÜ BAŞLAT ====
if not giris_kontrol():
    st.stop()

# ==== 5. SAYFA AYARLARI ====
st.set_page_config(
    page_title="Beykoz Haber Rapor Sistemi",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==== 6. ÇIKIŞ BUTONU ====
def cikis_butonu_ekle():
    with st.sidebar:
        if st.session_state.giris_yapildi:
            st.markdown("---")
            
            # Kullanıcı bilgisi
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown("👤")
            with col2:
                st.markdown(f"**{st.session_state.kullanici_isim}**")
                st.caption(f"@{st.session_state.kullanici_adi}")
                st.caption(f"Rol: {st.session_state.kullanici_rol}")
            
            # Oturum süresi
            if "giris_zamani" in st.session_state:
                fark = datetime.now() - st.session_state.giris_zamani
                dakika = int(fark.total_seconds() / 60)
                st.caption(f"🕒 {dakika} dakikadır oturum açık")
            
            st.markdown("---")
            
            # Çıkış butonu
            if st.button("🚪 **Güvenli Çıkış**", use_container_width=True, type="secondary"):
                st.session_state.giris_yapildi = False
                st.success("Başarıyla çıkış yaptınız!")
                time.sleep(1)
                st.rerun()

# ==================== SİSTEM AYARLARI ====================

# MÜDÜRLÜK LİSTESİ
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

# ==================== YARDIMCI FONKSİYONLAR ====================

def tarih_formatla(tarih_obj):
    """Tarihi güzel formatla"""
    if isinstance(tarih_obj, str):
        try:
            tarih_obj = datetime.strptime(tarih_obj, '%Y-%m-%d').date()
        except:
            try:
                tarih_obj = datetime.strptime(tarih_obj, '%d.%m.%Y').date()
            except:
                return str(tarih_obj)
    
    if hasattr(tarih_obj, 'strftime'):
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        gun_adi = gunler[tarih_obj.weekday()]
        return f"{tarih_obj.strftime('%d.%m.%Y')} {gun_adi}"
    
    return str(tarih_obj)

def veri_yukle():
    """Veritabanını yükle, yoksa oluştur"""
    if not os.path.exists(DOSYA_ADI):
        # Yeni veritabanı oluştur
        kolonlar = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
        df = pd.DataFrame(columns=kolonlar)
        df.to_csv(DOSYA_ADI, index=False, encoding='utf-8-sig')
        return df
    
    # Mevcut veritabanını oku
    try:
        df = pd.read_csv(DOSYA_ADI, encoding='utf-8-sig')
    except:
        df = pd.read_csv(DOSYA_ADI)
    
    return df.fillna("")

def veri_kaydet(tarih, mudurlukler, kaynak, sayi, ayrinti):
    """Yeni kayıt ekle"""
    kayitlar = []
    for mudurluk in mudurlukler:
        kayitlar.append({
            "Tarih": tarih,
            "Müdürlük": mudurluk,
            "Haber_Kaynagi": kaynak,
            "Sayı": sayi,
            "Ayrıntı": ayrinti,
            "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    yeni_df = pd.DataFrame(kayitlar)
    
    # CSV'ye ekle
    yeni_df.to_csv(DOSYA_ADI, mode='a', header=not os.path.exists(DOSYA_ADI), index=False, encoding='utf-8-sig')
    
    return len(kayitlar)

def kayit_formu_kaydet():
    """Formdaki verileri kaydet"""
    # Kontroller
    if not st.session_state.form_mudurlukler:
        st.error("❌ Lütfen en az bir müdürlük seçin!")
        return False
    
    # Kaynak kontrolü
    kaynak = st.session_state.form_kaynak
    if kaynak == "Diğer":
        diger_kaynak = st.session_state.diger_kaynak.strip()
        if not diger_kaynak:
            st.error("❌ Lütfen diğer kaynak için açıklama girin!")
            return False
        kaynak = diger_kaynak
    
    # Kaydet
    eklenen_sayi = veri_kaydet(
        st.session_state.form_tarih,
        st.session_state.form_mudurlukler,
        kaynak,
        st.session_state.form_sayi,
        st.session_state.form_ayrinti
    )
    
    # Başarı mesajı
    st.toast(f"✅ {eklenen_sayi} kayıt başarıyla eklendi!", icon="✅")
    
    # Formu temizle
    st.session_state.form_sayi = 1
    st.session_state.form_ayrinti = ""
    st.session_state.diger_kaynak = ""
    
    return True

# ==================== ANA UYGULAMA ====================

st.title("📊 BEYKOZ HABER TAKİP SİSTEMİ")
st.markdown("---")

# SİDEBAR - VERİ GİRİŞİ
with st.sidebar:
    st.header("📝 Yeni Kayıt")
    
    with st.form("yeni_kayit_formu", border=True):
        # Tarih
        st.date_input(
            "📅 Tarih",
            value=date.today(),
            format="DD/MM/YYYY",
            key="form_tarih"
        )
        
        # Müdürlük seçimi
        st.multiselect(
            "🏢 Müdürlükler",
            options=MUDURLUKLER,
            key="form_mudurlukler",
            placeholder="Seçiniz..."
        )
        
        # Kaynak
        kaynak_sec = st.selectbox(
            "📱 Kaynak",
            options=HABER_KAYNAKLARI,
            key="form_kaynak"
        )
        
        # Diğer kaynak
        if kaynak_sec == "Diğer":
            st.text_input(
                "✏️ Diğer Kaynak Adı",
                placeholder="Kaynak adını yazın...",
                key="diger_kaynak"
            )
        
        # Sayı
        st.number_input(
            "🔢 Haber/Sayı",
            min_value=1,
            value=1,
            key="form_sayi"
        )
        
        # Ayrıntı
        st.text_area(
            "📝 Ayrıntı / Şikayet",
            height=120,
            placeholder="Detayları yazın...",
            key="form_ayrinti"
        )
        
        # Kaydet butonu
        col1, col2 = st.columns(2)
        with col1:
            kaydet_btn = st.form_submit_button(
                "💾 KAYDET",
                type="primary",
                use_container_width=True
            )
        with col2:
            temizle_btn = st.form_submit_button(
                "🔄 TEMİZLE",
                type="secondary",
                use_container_width=True
            )
        
        if kaydet_btn:
            if kayit_formu_kaydet():
                st.rerun()
        
        if temizle_btn:
            st.session_state.form_sayi = 1
            st.session_state.form_ayrinti = ""
            st.session_state.diger_kaynak = ""
            st.rerun()

# ANA SAYFA İÇERİĞİ
# Verileri yükle
df = veri_yukle()

if not df.empty:
    try:
        df['Tarih'] = pd.to_datetime(df['Tarih']).dt.date
    except:
        pass

# FİLTRELEME PANELİ
st.subheader("🔍 Filtrele ve Rapor Al")

filtre_kolon1, filtre_kolon2, filtre_kolon3, filtre_kolon4 = st.columns(4)

with filtre_kolon1:
    baslangic_tarihi = st.date_input(
        "Başlangıç",
        value=date.today() - timedelta(days=7),
        format="DD/MM/YYYY"
    )

with filtre_kolon2:
    bitis_tarihi = st.date_input(
        "Bitiş",
        value=date.today(),
        format="DD/MM/YYYY"
    )

with filtre_kolon3:
    secilen_mudurlukler = st.multiselect(
        "Müdürlük",
        MUDURLUKLER,
        placeholder="Tümü"
    )

with filtre_kolon4:
    secilen_kaynaklar = st.multiselect(
        "Kaynak",
        HABER_KAYNAKLARI,
        placeholder="Tümü"
    )

# Verileri filtrele
if not df.empty:
    try:
        # Tarih filtresi
        mask = (df['Tarih'] >= baslangic_tarihi) & (df['Tarih'] <= bitis_tarihi)
        
        # Müdürlük filtresi
        if secilen_mudurlukler:
            mask &= df['Müdürlük'].isin(secilen_mudurlukler)
        
        # Kaynak filtresi
        if secilen_kaynaklar:
            mask &= df['Haber_Kaynagi'].isin(secilen_kaynaklar)
        
        filtrelenmis_df = df[mask].copy()
        
    except Exception as e:
        st.error(f"Filtreleme hatası: {e}")
        filtrelenmis_df = pd.DataFrame()
else:
    filtrelenmis_df = pd.DataFrame()

# İSTATİSTİK KARTLARI
if not filtrelenmis_df.empty:
    st.markdown("---")
    
    istatistik1, istatistik2, istatistik3, istatistik4 = st.columns(4)
    
    with istatistik1:
        toplam_kayit = len(filtrelenmis_df)
        toplam_sayi = filtrelenmis_df['Sayı'].sum()
        st.metric("📈 Toplam Haber", toplam_sayi, f"{toplam_kayit} kayıt")
    
    with istatistik2:
        mudurluk_sayisi = filtrelenmis_df['Müdürlük'].nunique()
        st.metric("🏢 Müdürlük Sayısı", mudurluk_sayisi)
    
    with istatistik3:
        kaynak_sayisi = filtrelenmis_df['Haber_Kaynagi'].nunique()
        st.metric("📱 Kaynak Sayısı", kaynak_sayisi)
    
    with istatistik4:
        gun_sayisi = filtrelenmis_df['Tarih'].nunique()
        st.metric("📅 Gün Sayısı", gun_sayisi)

# VERİ TABLOSU
st.markdown("---")
st.subheader("📋 Kayıtlar")

if not filtrelenmis_df.empty:
    # Düzenlenebilir tablo
    duzenlenmis_df = st.data_editor(
        filtrelenmis_df[['Tarih', 'Müdürlük', 'Haber_Kaynagi', 'Sayı', 'Ayrıntı']],
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Tarih": st.column_config.DateColumn(
                "Tarih",
                format="DD/MM/YYYY",
                required=True
            ),
            "Müdürlük": st.column_config.SelectboxColumn(
                "Müdürlük",
                options=MUDURLUKLER,
                required=True
            ),
            "Haber_Kaynagi": st.column_config.TextColumn(
                "Kaynak",
                required=True
            ),
            "Sayı": st.column_config.NumberColumn(
                "Sayı",
                min_value=1,
                required=True
            ),
            "Ayrıntı": st.column_config.TextColumn(
                "Ayrıntı",
                width="large"
            )
        }
    )
    
    # Değişiklikleri kaydet butonu
    if st.button("💾 Tablo Değişikliklerini Kaydet", type="primary"):
        try:
            # Orijinal indeksleri bul
            orijinal_indeksler = filtrelenmis_df.index
            
            # Yeni verileri hazırla
            for idx in orijinal_indeksler:
                if idx < len(duzenlenmis_df):
                    # Tarihi doğru formatta kaydet
                    tarih = duzenlenmis_df.iloc[idx]['Tarih']
                    if isinstance(tarih, pd.Timestamp):
                        tarih = tarih.date()
                    
                    df.loc[idx, 'Tarih'] = tarih
                    df.loc[idx, 'Müdürlük'] = duzenlenmis_df.iloc[idx]['Müdürlük']
                    df.loc[idx, 'Haber_Kaynagi'] = duzenlenmis_df.iloc[idx]['Haber_Kaynagi']
                    df.loc[idx, 'Sayı'] = duzenlenmis_df.iloc[idx]['Sayı']
                    df.loc[idx, 'Ayrıntı'] = duzenlenmis_df.iloc[idx]['Ayrıntı']
            
            # CSV'ye kaydet
            df.to_csv(DOSYA_ADI, index=False, encoding='utf-8-sig')
            st.success("✅ Değişiklikler kaydedildi!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Kaydetme hatası: {e}")
    
    # EXCEL İNDİR BUTONU
    st.markdown("---")
    st.subheader("📊 Raporlar")
    
    rapor_kolon1, rapor_kolon2, rapor_kolon3 = st.columns(3)
    
    with rapor_kolon1:
        # Excel indir
        if not filtrelenmis_df.empty:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                filtrelenmis_df.to_excel(writer, index=False, sheet_name='Rapor')
                
                # Formatlama
                workbook = writer.book
                worksheet = writer.sheets['Rapor']
                
                # Başlık formatı
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
                
                # Başlıkları formatla
                for col_num, value in enumerate(filtrelenmis_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
            
            excel_data = excel_buffer.getvalue()
            
            st.download_button(
                label="📥 Excel İndir",
                data=excel_data,
                file_name=f"beykoz_rapor_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
    
    with rapor_kolon2:
        # CSV indir
        if not filtrelenmis_df.empty:
            csv_data = filtrelenmis_df.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="📄 CSV İndir",
                data=csv_data,
                file_name=f"beykoz_rapor_{date.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with rapor_kolon3:
        # Verileri sıfırla butonu (sadece admin)
        if st.session_state.kullanici_rol == "admin":
            if st.button("⚠️ Verileri Temizle", use_container_width=True, type="secondary"):
                if st.checkbox("Emin misiniz? Bu işlem geri alınamaz!"):
                    # Boş veritabanı oluştur
                    kolonlar = ["Tarih", "Müdürlük", "Haber_Kaynagi", "Sayı", "Ayrıntı", "Kayit_Zamani"]
                    bos_df = pd.DataFrame(columns=kolonlar)
                    bos_df.to_csv(DOSYA_ADI, index=False, encoding='utf-8-sig')
                    st.success("✅ Veritabanı temizlendi!")
                    time.sleep(2)
                    st.rerun()
    
    # GRAFİKLER
    st.markdown("---")
    st.subheader("📈 Görselleştirme")
    
    graf_kolon1, graf_kolon2 = st.columns(2)
    
    with graf_kolon1:
        st.caption("🏢 Müdürlüklere Göre Dağılım")
        if not filtrelenmis_df.empty:
            mudurluk_dagilim = filtrelenmis_df.groupby('Müdürlük')['Sayı'].sum().sort_values()
            if not mudurluk_dagilim.empty:
                st.bar_chart(mudurluk_dagilim)
    
    with graf_kolon2:
        st.caption("📅 Tarihlere Göre Dağılım")
        if not filtrelenmis_df.empty:
            # Tarih formatını düzelt
            try:
                tarih_dagilim = filtrelenmis_df.copy()
                tarih_dagilim['Tarih'] = pd.to_datetime(tarih_dagilim['Tarih'])
                tarih_dagilim = tarih_dagilim.groupby(tarih_dagilim['Tarih'].dt.date)['Sayı'].sum()
                if not tarih_dagilim.empty:
                    st.line_chart(tarih_dagilim)
            except:
                pass

else:
    # VERİ YOKSA
    st.info("ℹ️ Bu filtrelerle eşleşen kayıt bulunamadı.")
    
    # Örnek veri ekle butonu (sadece admin)
    if st.session_state.kullanici_rol == "admin" and st.button("Örnek Veri Ekle"):
        ornek_veriler = [
            {
                "Tarih": date.today(),
                "Müdürlük": "Fen İşleri Müdürlüğü",
                "Haber_Kaynagi": "Beykoz Anlık",
                "Sayı": 2,
                "Ayrıntı": "Yol çalışması hakkında şikayet",
                "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "Tarih": date.today() - timedelta(days=1),
                "Müdürlük": "Temizlik İşleri Müdürlüğü",
                "Haber_Kaynagi": "Beykoz Burada",
                "Sayı": 1,
                "Ayrıntı": "Çöp toplama saatleri ile ilgili öneri",
                "Kayit_Zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
        
        ornek_df = pd.DataFrame(ornek_veriler)
        ornek_df.to_csv(DOSYA_ADI, mode='a', header=not os.path.exists(DOSYA_ADI), index=False, encoding='utf-8-sig')
        
        st.success("✅ Örnek veriler eklendi!")
        st.rerun()

# ==== ÇIKIŞ BUTONUNU ÇAĞIR ====
cikis_butonu_ekle()

# ==== ALT BİLGİ ====
st.markdown("---")

st.caption(f"© 2026 MAB • Kullanıcı: {st.session_state.kullanici_isim} • Son güncelleme: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
