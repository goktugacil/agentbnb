from flask import Flask, request, jsonify
import pandas as pd
import joblib
import numpy as np
import os

app = Flask(__name__)

GOOGLE_SHEETS_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQtk-7eRprKONHH1LONCddSowpZ85UOnlyYlpA3F5uNiSdU0IgiiacjQuRCY3wGuddbk7ePltMhc00G/"
    "pub?output=csv"
)

# Model yükleniyor
model = joblib.load('price_model.pkl')

# Veri çekiliyor
df = pd.read_csv(GOOGLE_SHEETS_CSV_URL, low_memory=False, decimal=',')

df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

if 'id' not in df.columns:
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'id'}, inplace=True)

model_features = model.get_booster().feature_names

def get_location_comment(district):
    """geo_cluster numarasına göre açıklama üretir."""
    cluster_comments = {
        '0': "turistler için çok cazip bir bölge.",
        '1': "şehir merkezine yakın ve popüler bir alan.",
        '2': "sessiz ve yerel bir mahalle.",
        '3': "şehir dışına yakın, daha sakin bir bölge.",
        '4': "turist yoğunluğu az, yerel yaşam odaklı bir mahalle.",
        '5': "denize yakın konumu ile dikkat çeken bir alan.",
    }
    return cluster_comments.get(str(district), "konum bilgisi güncelleniyor.")

def calculate_superhost_status(row):
    """
    Airbnb'nin kriterlerine göre Superhost olup olmadığını tahmin eder.
    Tür dönüşümü ile daha güvenli hale getirildi.
    """
    try:
        rating = float(row.get('review_scores_rating', 0))
    except (ValueError, TypeError):
        rating = 0

    try:
        num_reviews = int(row.get('number_of_reviews', 0))
    except (ValueError, TypeError):
        num_reviews = 0

    try:
        availability = int(row.get('availability_365', 0))
    except (ValueError, TypeError):
        availability = 0

    is_superhost = False
    strategies = []

    if rating >= 4.8 and num_reviews >= 10 and availability >= 200:
        is_superhost = True
    else:
        if rating < 4.8:
            strategies.append("Misafir yorumlarını iyileştirerek genel puanınızı 4.8 üzerine çıkarın.")
        if num_reviews < 10:
            strategies.append("Daha fazla rezervasyon alarak en az 10 yorum toplayın.")
        if availability < 200:
            strategies.append("Ev müsaitlik günlerinizi artırarak daha fazla rezervasyon fırsatı yaratın.")

    return is_superhost, strategies

@app.route('/get_property', methods=['GET'])
def get_property():
    try:
        property_id = request.args.get('id', type=int)
        print(f"İstek alındı! ID: {property_id}")

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
        prediction_real = np.expm1(prediction)

        district = str(prop['geo_cluster'].iloc[0]) if 'geo_cluster' in prop else None
        accommodates = int(prop['accommodates'].iloc[0])
        latitude = float(prop['latitude'].iloc[0])
        longitude = float(prop['longitude'].iloc[0])

        # Superhost durumu hesaplama
        is_superhost, strategies = calculate_superhost_status(prop.iloc[0])

        if is_superhost:
            superhost_comment = "⭐ Tebrikler! Şu anda Superhostsunuz!"
        else:
            superhost_comment = "🛠️ Henüz Superhost değilsiniz. İşte geliştirme önerileriniz:"

        professional_advice = "Performansınız iyi gözüküyor, devam edin!"
        location_comment = get_location_comment(district)

        return jsonify({
            'prediction': round(float(prediction_real), 2),
            'district': district,
            'accommodates': accommodates,
            'latitude': latitude,
            'longitude': longitude,
            'superhost_comment': superhost_comment,
            'strategies': strategies,
            'professional_advice': professional_advice,
            'location_comment': location_comment
        })

    except Exception as e:
        return jsonify({'error': f'İşlem sırasında hata: {e}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)