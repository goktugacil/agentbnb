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

        review_count = prop['number_of_reviews'].iloc[0]
        availability = prop['availability_365'].iloc[0]
        host_response_rate = prop.get('host_response_rate', pd.Series([0])).iloc[0]

        # Superhost skor % üzerinden normalize ediliyor
        superhost_score = 0
        if host_response_rate:
            superhost_score += host_response_rate * 0.4
        if review_count:
            superhost_score += min(review_count, 100) * 0.3
        if availability:
            superhost_score += (availability / 365) * 30
        superhost_score = min(superhost_score, 100)
        superhost_score = round(superhost_score, 2)

        # Superhost yorumu
        if superhost_score >= 80:
            superhost_comment = "⭐ Tebrikler! Superhost potansiyeline çok yakınsınız!"
        elif superhost_score >= 50:
            superhost_comment = "😊 İyi gidiyorsunuz! Birkaç küçük iyileştirme ile Superhost olabilirsiniz."
        else:
            superhost_comment = "🛠️ Daha fazla yorum ve hızlı cevaplarla Superhost olabilirsiniz."

        professional_advice = "Performansınız iyi gözüküyor, devam edin!"
        location_comment = get_location_comment(district)

        return jsonify({
            'prediction': round(float(prediction_real), 2),
            'district': district,
            'accommodates': accommodates,
            'latitude': latitude,
            'longitude': longitude,
            'superhost_score': superhost_score,
            'superhost_comment': superhost_comment,
            'professional_advice': professional_advice,
            'location_comment': location_comment
        })

    except Exception as e:
        return jsonify({'error': f'İşlem sırasında hata: {e}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)