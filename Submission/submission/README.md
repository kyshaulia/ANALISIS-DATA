# Proyek Analisis Data: Bike Sharing Dataset 🚲

Analisis pola penyewaan sepeda Capital Bikeshare (Washington D.C., 2011–2012) beserta dashboard interaktif Streamlit.

## Pertanyaan Bisnis
1. Pada jam berapa penyewaan memuncak di hari kerja vs akhir pekan/libur (2011–2012), dan berapa selisihnya?
2. Seberapa besar cuaca (berkabut/hujan ringan vs cerah) dan rentang suhu memengaruhi rata-rata penyewaan harian?
3. Berapa pertumbuhan penyewaan bulanan 2012 vs 2011 (YoY) dan berapa porsi pengguna kasual per musim?

Teknik analisis lanjutan: **Manual Grouping** (segmen waktu) dan **Binning** (`pd.cut` untuk suhu dan tier permintaan).

## Struktur Direktori
```
submission
├───dashboard
│   ├───main_data.csv      # data harian yang sudah dibersihkan
│   ├───hour_data.csv      # data per jam yang sudah dibersihkan
│   └───dashboard.py
├───data
│   ├───day.csv
│   ├───hour.csv
│   └───Readme.txt
├───notebook.ipynb
├───README.md
├───requirements.txt
└───url.txt
```

## Setup Environment

Shell/Terminal:
```
mkdir proyek_analisis_data
cd proyek_analisis_data
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Menjalankan Dashboard
Dari folder utama proyek:
```
streamlit run dashboard/dashboard.py
```
Dashboard terbuka di `http://localhost:8501`.

## Menjalankan Notebook
Buka `notebook.ipynb` dari folder utama proyek (agar path `data/` dan `dashboard/` terbaca), lalu jalankan semua sel. Menjalankan notebook akan menghasilkan ulang `dashboard/main_data.csv` dan `dashboard/hour_data.csv`.

## Deploy ke Streamlit Community Cloud
1. Unggah folder proyek ke repositori GitHub publik.
2. Di https://share.streamlit.io pilih **New app**, pilih repositori tersebut.
3. Isi **Main file path** dengan `dashboard/dashboard.py`, lalu **Deploy**.
4. Tulis tautan hasilnya di `url.txt`.

## Sumber Data
Fanaee-T, H. & Gama, J. (2013). *Event labeling combining ensemble detectors and background knowledge.* Progress in Artificial Intelligence.
