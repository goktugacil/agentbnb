from flask import Flask, request, jsonify
import pandas as pd
import joblib
import numpy as np
import math

app = Flask(__name__)

GOOGLE_SHEETS_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQtk-7eRprKONHH1LONCddSowpZ85UOnlyYlpA3F5uNiSdU0IgiiacjQuRCY3wGuddbk7ePltMhc00G/"
    "pub?output=csv"
)

model = joblib.load('price_model.pkl')

# 🌟 Değişiklik: decimal=',' var.
df = pd.read_csv(GOOGLE_SHEETS_CSV_URL, low_memory=False, decimal=',')

# latitude/longitude mutlaka sayısal
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

if 'id' not in df.columns:
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'id'}, inplace=True)

model_features = model.get_booster().feature_names

@app.route('/get_property', methods=['GET'])
def get_property():
    try:
        property_id = request.args.get('id', type=int)
        if property_id is None:
            return jsonify({'error': 'Geçerli bir id parametresi sağlayın.'}), 400

        prop = df[df['id'] == property_id]
        if prop.empty:
            return jsonify({'error': 'Bu ID ile eşleşen bir kayıt bulunamadı.'}), 404

        features = prop.drop(columns=['id', 'price'], errors='ignore').copy()
        for col in model_features:
            if col not in features.columns:
                features[col] = 0
        features = features[model_features]
        features = features.apply(pd.to_numeric, errors='coerce')

        prediction = model.predict(features)[0]
        prediction_real = np.expm1(prediction)  # 🔥 LOG dönüşümünü açıyoruz

        district = str(prop['geo_cluster'].iloc[0]) if 'geo_cluster' in prop else None
        accommodates = int(prop['accommodates'].iloc[0])
        latitude = float(prop['latitude'].iloc[0])
        longitude = float(prop['longitude'].iloc[0])

        # Superhost Hesabı (normalize 0–100 arası)
        review_count = prop['number_of_reviews'].iloc[0]
        availability = prop['availability_365'].iloc[0]
        host_response_rate = prop.get('host_response_rate', pd.Series([0])).iloc[0]

        superhost_raw_score = 0
        if host_response_rate:
            superhost_raw_score += (host_response_rate / 100) * 2
        if review_count:
            superhost_raw_score += min(review_count / 100, 2)
        if availability:
            superhost_raw_score += (availability / 365) * 2

        superhost_score_normalized = round((superhost_raw_score / 6) * 100, 2)

        # Rating kontrolü
        review_scores_rating_fixed = prop.get('review_scores_rating_fixed', pd.Series([0])).iloc[0]
        meets_superhost_rating = False
        if review_scores_rating_fixed and review_scores_rating_fixed >= 4.8:
            meets_superhost_rating = True

        # Tavsiye Mesajı
        professional_advice = "Performansınız iyi gözüküyor, devam edin!"
        if not meets_superhost_rating:
            professional_advice = "Superhost olmak için genel değerlendirme puanınızı 4.8'in üzerine çıkarmalısınız."
        elif reviews := prop['number_of_reviews'].iloc[0] < 10:
            professional_advice = "Superhost olmak için en az 10 rezervasyon veya 100 gece kiralama yapmalısınız."
        elif host_response_rate < 90:
            professional_advice = "Superhost olmak için cevap oranınızı %90'ın üstüne çıkarmalısınız."

        return jsonify({
            'prediction': round(float(prediction_real), 2),
            'district': district,
            'accommodates': accommodates,
            'latitude': latitude,
            'longitude': longitude,
            'superhost_score_normalized': superhost_score_normalized,
            'review_scores_rating_fixed': review_scores_rating_fixed,
            'meets_superhost_rating_criteria': meets_superhost_rating,
            'professional_advice': professional_advice
        })

    except Exception as e:
        return jsonify({'error': f'İşlem sırasında hata: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)