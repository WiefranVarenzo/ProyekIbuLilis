import pandas as pd
import streamlit as st

# Fungsi untuk memuat dan membagi data berdasarkan 'KOTA/KABUPATEN'
def bagi_data_per_kota_kabupaten(df):
    # Buat list unik dari 'KOTA/KABUPATEN'
    kota_kabupaten_list = df['KOTA/KABUPATEN'].unique()
    
    # Kamus untuk menyimpan dataframe berdasarkan KOTA/KABUPATEN
    kota_kabupaten_dfs = {}
    
    # Hitung nilai minimum dan maksimum untuk setiap indikator di seluruh dataset
    min_values = df.select_dtypes(include='number').min()
    max_values = df.select_dtypes(include='number').max()

    # Definisikan bobot untuk setiap indikator
    bobot_data = [5, 5, 4, 4, 4, 5, 5, 4, 5, 4,
                  4, 4, 3, 4, 4, 5, 4, 4, 4, 3,
                  5, 5, 4, 4, 4, 3, 4, 5, 4, 4,
                  5, 5, 5, 2, 2, 3, 4, 3, 2]

    # Kategori berdasarkan indeks kolom
    kategori = [
        "Kesehatan Balita",  # Indeks 0 - 4
        "Kesehatan Reproduksi",  # Indeks 5 - 9
        "Pelayanan Kesehatan",  # Indeks 10 - 21
        "Penyakit Tidak Menular",  # Indeks 22 - 27
        "Penyakit Menular",  # Indeks 28 - 35
        "Sanitasi dan Keadaan Lingkungan"  # Indeks 36 dan seterusnya
    ]

    # Loop untuk membagi data berdasarkan KOTA/KABUPATEN
    for i, kota_kabupaten in enumerate(kota_kabupaten_list, start=1):
        # Filter dataframe berdasarkan KOTA/KABUPATEN
        sub_df = df[df['KOTA/KABUPATEN'] == kota_kabupaten]
        
        # Buat nama variabel seperti 'KOTA_KAB1', 'KOTA_KAB2', dst.
        var_name = f"KOTA_KAB{i}"
        
        # Simpan dataframe ke dalam kamus
        kota_kabupaten_dfs[var_name] = sub_df
        
        # Tampilkan nama variabel dan dataframe-nya di Streamlit
        st.write(f"Dataframe untuk {kota_kabupaten} (nama variabel: {var_name}):")
        st.dataframe(sub_df.head())  # Tampilkan 5 baris pertama di Streamlit
        
        # Pilih hanya kolom numeric untuk menghitung rata-rata
        numeric_cols = sub_df.select_dtypes(include='number')
        
        # Menghitung rata-rata untuk setiap kolom numeric
        averages = numeric_cols.mean()
        
        # Buat dataframe untuk menyimpan hasil rata-rata dan penyetaraan positif
        indikator_df = pd.DataFrame({
            'Nama Indikator': averages.index,
            'Nilai Indikator': averages.values,
            'Penyetaraan Positif': [100 - value if value < 50 else value for value in averages.values],
        })

        # Tambahkan kolom Bobot menggunakan indeks kolom
        indikator_df['Bobot'] = bobot_data[:len(indikator_df)]

        # Menghitung Indeks Indikator dengan rumus Min-Max
        indikator_df['Indeks Indikator'] = (indikator_df['Nilai Indikator'] - min_values[indikator_df['Nama Indikator'].values].values) / (max_values[indikator_df['Nama Indikator'].values].values - min_values[indikator_df['Nama Indikator'].values].values)

        # Tambahkan kolom Kategori
        kategori_labels = []
        for index in range(len(indikator_df)):
            if index <= 4:
                kategori_labels.append(kategori[0])
            elif index <= 9:
                kategori_labels.append(kategori[1])
            elif index <= 21:
                kategori_labels.append(kategori[2])
            elif index <= 27:
                kategori_labels.append(kategori[3])
            elif index <= 35:
                kategori_labels.append(kategori[4])
            else:
                kategori_labels.append(kategori[5])

        indikator_df['Kategori'] = kategori_labels

        # Reset indeks kelompok indikator setiap loop
        indeks_kelompok = {kat: 0 for kat in kategori}
        
        # Menghitung total bobot per kategori
        kategori_total_bobot = indikator_df.groupby('Kategori')['Bobot'].transform('sum')

        # Menghitung proporsi bobot (bobot indikator saat ini / total bobot kategori)
        indikator_df['Proporsi Bobot'] = indikator_df['Bobot'] / kategori_total_bobot

        # Hitung Indeks Kelompok Indikator per kategori
        for kat in kategori:
            if kat in indikator_df['Kategori'].values:
                indeks_kelompok[kat] = (indikator_df.loc[indikator_df['Kategori'] == kat, 'Indeks Indikator'] * indikator_df.loc[indikator_df['Kategori'] == kat, 'Proporsi Bobot']).sum()

        # Tambahkan kolom Indeks Kelompok Indikator ke dataframe
        indikator_df['Indeks Kelompok Indikator'] = indikator_df['Kategori'].map(indeks_kelompok)

        # Hitung IPKD
        ipkd = sum(indeks_kelompok.values()) / len(kategori)

        # Tampilkan tabel hasil
        st.write(f"Tabel Hasil Indikator untuk {kota_kabupaten}:")
        st.dataframe(indikator_df)  # Tampilkan tabel hasil di Streamlit
        
        # Tampilkan nilai IPKD di bawah tabel hasil
        st.write(f"Nilai IPKD untuk {kota_kabupaten}: {ipkd:.3f}")

    return kota_kabupaten_dfs

# URL file CSV yang akan digunakan
st.title("Analisis Data Kesehatan")
url = "https://raw.githubusercontent.com/WiefranVarenzo/ProyekBuLilis/refs/heads/master/Dataset_model/DFterbaru%20(4).csv"

# Baca file CSV dari URL
df = pd.read_csv(url)

# Panggil fungsi dan tampilkan data di Streamlit
kota_kabupaten_dfs = bagi_data_per_kota_kabupaten(df)
