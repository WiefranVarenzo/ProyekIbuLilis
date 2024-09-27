import streamlit as st
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
from sklearn.pipeline import Pipeline

# Fungsi untuk memuat model pipeline
def load_pipeline(model_name):
    return joblib.load(model_name)

# Fungsi untuk memuat dan memproses dataset
def process_data(data):
    # Ubah nama kolom dari kolom ke-4 dan seterusnya, ambil sampai kolom sebelum terakhir
    original_names = list(data.columns[3:-1])  # Simpan nama asli kolom sampai kolom sebelum terakhir
    new_column_names = list(data.columns[:3]) + [f'C{i-2}' for i in range(3, data.shape[1])]  # Ubah nama kolom
    data.columns = new_column_names
    
    # Drop kolom yang tidak diperlukan
    X = data.drop(columns=['C40', 'TAHUN', 'KOTA/KABUPATEN', 'PROVINSI'])  # Ganti dengan nama kolom yang sesuai
    y = data['C40']  # Ganti dengan nama kolom yang sesuai
    
    return X, y, original_names

# Fungsi untuk menampilkan ranking berdasarkan Permutation Importance
def rank_features(importance, feature_names, original_names, model_option):
    importance_df = pd.DataFrame({
        'Importance': importance,
        'Nama Indikator': original_names,
        'Kode': feature_names
    })
    
    # Add "kategori bobot" column for Enhanced Random Forest model
    if model_option == "Enhanced Random Forest":
        conditions = [
            (importance_df['Importance'] > 0.03),
            (importance_df['Importance'] >= 0.015) & (importance_df['Importance'] <= 0.03),
            (importance_df['Importance'] < 0.015)
        ]
        choices = ['Mutlak', 'Penting', 'Perlu']
        importance_df['Kategori Bobot'] = np.select(conditions, choices, default='')

    # Sort berdasarkan importance dan tambahkan kolom ranking
    importance_df = importance_df.sort_values(by='Importance', ascending=False)
    importance_df['Ranking'] = range(1, len(original_names) + 1)
    
    if model_option == "Enhanced Random Forest":
        return importance_df[['Ranking', 'Nama Indikator', 'Kode', 'Importance', 'Kategori Bobot']]
    else:
        return importance_df[['Ranking', 'Nama Indikator', 'Kode', 'Importance']]

# Fungsi untuk menghitung dan menampilkan metrik evaluasi
def evaluate_model(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    return r2, mae, mse, rmse

# Halaman utama aplikasi Streamlit
st.title("Model Prediksi dan Analisis Permutation Importance")

# Upload dataset
uploaded_file = st.file_uploader("Upload CSV file", type="csv")

if uploaded_file is not None:
    # Baca dataset
    data = pd.read_csv(uploaded_file)

    # Proses data dan ganti nama kolom
    X, y, original_names = process_data(data)

    # Pilih model yang akan digunakan
    model_option = st.selectbox(
        "Pilih Model",
        ["Random Forest", "Gradient Boosting", "Decision Tree", "SVM", "Enhanced Random Forest"]
    )

    # Load model pipeline yang dipilih
    model_file = f"model_{model_option.lower().replace(' ', '_')}.pkl"  # Gunakan pipeline
    pipeline = load_pipeline(model_file)

    # Prediksi hasil menggunakan model pipeline yang dipilih
    predictions = pipeline.predict(X)  # X sudah diproses

    # Lakukan Permutation Importance
    perm_importance = permutation_importance(pipeline, X, y, n_repeats=10, random_state=42)

    # Scatter plot Permutation Importance
    st.subheader(f"Permutation Importance for {model_option}")
    plt.figure(figsize=(10, 6))
    plt.scatter(X.columns, perm_importance.importances_mean, s=100, alpha=0.6)
    plt.title(f"Permutation Importance for {model_option}")
    plt.xlabel("Indikator")
    plt.ylabel("Importance")
    plt.xticks(rotation=45)
    st.pyplot(plt)

    # Ranking indikator berdasarkan Permutation Importance
    importance_df = rank_features(perm_importance.importances_mean, X.columns, original_names, model_option)
    st.subheader("Ranking Indikator Berdasarkan Permutation Importance")
    st.dataframe(importance_df)

    # Metrik evaluasi
    r2, mae, mse, rmse = evaluate_model(y, predictions)
    st.subheader("Model Evaluation Metrics")
    st.write(f"R²: {r2:.4f}")
    st.write(f"Mean Absolute Error (MAE): {mae:.4f}")
    st.write(f"Mean Squared Error (MSE): {mse:.4f}")
    st.write(f"Root Mean Squared Error (RMSE): {rmse:.4f}")

    # Scatter plot Actual vs Predicted
    st.subheader("Grafik Actual vs Predicted")
    plt.figure(figsize=(8, 6))
    plt.scatter(y, predictions, alpha=0.6, color='red')
    plt.plot([y.min(), y.max()], [y.min(), y.max()], 'k--', lw=2)
    plt.title(f"Actual vs Predicted for {model_option}")
    plt.xlabel("Actual Values")
    plt.ylabel("Predicted Values")
    st.pyplot(plt)
