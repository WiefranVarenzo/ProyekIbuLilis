import pandas as pd
import streamlit as st
import io
import xlsxwriter

# Fungsi untuk memuat dan membagi data berdasarkan 'KOTA/KABUPATEN' dan 'TAHUN'
def bagi_data_per_kota_kabupaten_dan_tahun(df):
    # Buat list unik dari 'KOTA/KABUPATEN'
    kota_kabupaten_list = df['KOTA/KABUPATEN'].unique()
    
    # Kamus untuk menyimpan dataframe berdasarkan KOTA/KABUPATEN dan TAHUN
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
        "Penyakit Menular",  # Indeks 28 - 33
        "Sanitasi dan Keadaan Lingkungan Hidup"  # Indeks 34 dan seterusnya
    ]

    # Loop untuk membagi data berdasarkan KOTA/KABUPATEN
    for kota_kabupaten in kota_kabupaten_list:
        # Filter dataframe berdasarkan KOTA/KABUPATEN
        sub_df = df[df['KOTA/KABUPATEN'] == kota_kabupaten]
        
        # Buat list unik dari 'TAHUN'
        tahun_list = sub_df['TAHUN'].unique()
        
        # Loop untuk membagi data berdasarkan TAHUN
        for tahun in tahun_list:
            # Filter dataframe berdasarkan tahun
            sub_df_tahun = sub_df[sub_df['TAHUN'] == tahun]
            
            # Buat nama variabel seperti 'KotaKabupaten_2020'
            var_name = f"{kota_kabupaten}_{tahun}"
            
            # Tampilkan nama variabel dan dataframe-nya di Streamlit
            st.write(f"Dataframe untuk {kota_kabupaten} tahun {tahun} (nama variabel: {var_name}):")
            st.dataframe(sub_df_tahun.head())  # Tampilkan 5 baris pertama di Streamlit
            
            # Pilih hanya kolom numeric untuk menghitung nilai indikator
            numeric_cols = sub_df_tahun.select_dtypes(include='number')

            # Filter out the indicators with weight 2
            valid_indices = [i for i, weight in enumerate(bobot_data) if weight != 2]
            filtered_numeric_cols = numeric_cols.iloc[:, valid_indices]

            # Buat dataframe untuk menyimpan hasil nilai indikator dan penyetaraan positif
            indikator_df = pd.DataFrame({
                'Nama Indikator': filtered_numeric_cols.columns,
                'Nilai Indikator': filtered_numeric_cols.mean().values,  # Ambil rata-rata per indikator untuk tahun tersebut
                'Penyetaraan Positif': [100 - value if value < 50 else value for value in filtered_numeric_cols.mean().values],
            })

            # Tambahkan kolom Bobot menggunakan indeks kolom yang valid
            indikator_df['Bobot'] = [bobot_data[i] for i in valid_indices]

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
                elif index <= 33:
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
            st.write(f"Tabel Hasil Indikator untuk {kota_kabupaten} tahun {tahun}:")
            st.dataframe(indikator_df)  # Tampilkan tabel hasil di Streamlit
            
            # Tampilkan nilai IPKD di bawah tabel hasil
            st.write(f"Nilai IPKD untuk {kota_kabupaten} tahun {tahun}: {ipkd:.3f}")

            # Simpan nilai IPKD ke dalam dataframe
            indikator_df['Nilai IPKD'] = ipkd
            
            # Simpan dataframe hasil perhitungan ke dalam kamus
            kota_kabupaten_dfs[var_name] = indikator_df

    # Tambahkan tabel ringkasan hasil akhir
    hasil_akhir_df = pd.DataFrame(columns=["Kota/Kabupaten", "Tahun", "Kesehatan Balita", 
                                            "Kesehatan Reproduksi", "Pelayanan Kesehatan", 
                                            "Penyakit Tidak Menular", "Penyakit Menular", 
                                            "Sanitasi dan Keadaan Lingkungan Hidup", "Nilai IPKD"])

    # Loop untuk mengumpulkan data ke dalam hasil_akhir_df
    for kota_kabupaten, df in kota_kabupaten_dfs.items():
        # Ambil nama kota/kabupaten dan tahun dari variabel
        kota, tahun = kota_kabupaten.split('_')
        
        # Ambil nilai indeks kelompok per kategori
        nilai_kategori = []
        for kat in kategori:  # Gunakan semua kategori
            if kat in df['Kategori'].values:
                nilai_kategori.append(df.loc[df['Kategori'] == kat, 'Indeks Kelompok Indikator'].values[0])
            else:
                nilai_kategori.append(0)  # Jika tidak ada nilai, gunakan 0

        # Hitung nilai IPKD
        ipkd = df['Nilai IPKD'].iloc[0]  # Ambil nilai IPKD dari df
        
        # Buat DataFrame untuk baris baru
        baris_baru = pd.DataFrame({
            "Kota/Kabupaten": [kota],
            "Tahun": [tahun],
            **{kategori[i]: [nilai_kategori[i]] for i in range(len(nilai_kategori))},
            "Nilai IPKD": [ipkd]
        })

        # Gabungkan dengan hasil_akhir_df
        hasil_akhir_df = pd.concat([hasil_akhir_df, baris_baru], ignore_index=True)

    # Urutkan berdasarkan tahun
    hasil_akhir_df = hasil_akhir_df.sort_values(by=["Kota/Kabupaten", "Tahun"])

    # Tampilkan hasil akhir di Streamlit
    st.write("Tabel Hasil Akhir IPKD:")
    st.dataframe(hasil_akhir_df)

    # Simpan hasil akhir ke dalam kamus jika diperlukan untuk ekspor
    kota_kabupaten_dfs["Hasil_Akhir"] = hasil_akhir_df

    return kota_kabupaten_dfs

# Fungsi untuk mendownload data dalam bentuk Excel
def download_excel(kota_kabupaten_dfs):
    output = io.BytesIO()  # Buat buffer untuk menyimpan file Excel
    
    # Buat workbook baru
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for kota_kabupaten, df in kota_kabupaten_dfs.items():
            # Simpan setiap dataframe per kota/kabupaten per tahun di sheet Excel terpisah
            # Gantilah '/' dalam nama kota/kabupaten dengan '_' agar nama sheet valid
            safe_sheet_name = kota_kabupaten.replace('/', '_')
            df.to_excel(writer, sheet_name=safe_sheet_name[:31], index=False)  # Batasan panjang nama sheet adalah 31 karakter
    
    # Dapatkan konten dari output buffer
    output.seek(0)
    
    # Tampilkan tombol download di Streamlit
    st.download_button(
        label="Download data IPKD dalam Excel",
        data=output,
        file_name="IPKD_perhitungan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# URL file CSV yang akan digunakan
st.title("Analisis Data Kesehatan")

# Tombol download Excel di bagian atas
st.subheader("Unduh Hasil Perhitungan IPKD dalam Excel")
url = "https://raw.githubusercontent.com/WiefranVarenzo/ProyekBuLilis/refs/heads/master/Dataset_model/DFterbaru%20(4).csv"

# Baca file CSV dari URL
df = pd.read_csv(url)

# Panggil fungsi dan tampilkan data di Streamlit
kota_kabupaten_dfs = bagi_data_per_kota_kabupaten_dan_tahun(df)

# Panggil fungsi untuk download data dalam bentuk Excel
download_excel(kota_kabupaten_dfs)
