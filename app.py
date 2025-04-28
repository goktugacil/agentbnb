from flask import Flask, request, jsonify
import pandas as pd
import joblib
import numpy as np
import math

app = Flask(__name__)

# Google Sheets’ten veriyi oku
GOOGLE_SHEETS_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQtk-7eRprKONHH1LONCddSowpZ85UOnlyYlpA3F5uNiSdU0IgiiacjQuRCY3wGuddbk7ePltMhc00G/"
    "pub?output=csv"
)

model = joblib.load('price_model.pkl')
df = pd.read_csv(GOOGLE_SHEETS_CSV_URL, low_memory=False)

# 🛠 id sütununu düzeltiyoruz
df['id'] = df['id'].astype(str).str.strip()    # id’leri string yap ve boşlukları kaldır
df['id'] = pd.to_numeric(df['id'], errors='coerce')  # sayıya çevir
df.dropna(subset=['id'], inplace=True)
df['id'] = df['id'].astype(int)

# Latitude ve longitude güvenli olsun
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')

# Model özelliklerini al
model_features = model.get_booster().feature_names

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

@app.route('/get_property', methods=['GET'])
def get_property():
    try:
        property_id = request.args.get('id', type=int)
        if property_id is None:
            return jsonify({'error': 'Geçerli bir id parametresi sağlayın.'}), 400

        # 🔥 ID eşleşmesi artık doğru çalışacak
        prop = df[df['id'] == property_id]
        if prop.empty:
            return jsonify({'error': 'Bu ID ile eşleşen bir kayıt bulunamadı.'}), 404

        # Özellikleri hazırla
        features = prop.drop(columns=['id', 'price'], errors='ignore').copy()
        for col in model_features:
            if col not in features.columns:
                features[col] = 0
        features = features[model_features]
        features = features.apply(pd.to_numeric, errors='coerce')

        prediction = model.predict(features)[0]

        # İlave bilgiler
        district = str(prop['geo_cluster'].iloc[0]) if 'geo_cluster' in prop else None
        accommodates = int(prop['accommodates'].iloc[0])
        latitude = float(prop['latitude'].iloc[0])
        longitude = float(prop['longitude'].iloc[0])

        # Süperhost skor
        reviews = prop['number_of_reviews'].iloc[0]
        availability = prop['availability_365'].iloc[0]
        response_rate = prop.get('host_response_rate', pd.Series([0])).iloc[0]

        score = 0.0
        score += (response_rate/100)*2 if response_rate else 0
        score += min(reviews/100, 2) if reviews else 0
        score += (availability/365)*2 if availability else 0
        superhost_score = round(score, 2)

        return jsonify({
            'prediction': round(float(prediction), 2),
            'district': district,
            'accommodates': accommodates,
            'latitude': latitude,
            'longitude': longitude,
            'superhost_score': superhost_score,
            'professional_advice': "Performansınız iyi gözüküyor, devam edin!"
        })

    except Exception as e:
        return jsonify({'error': f'İşlem sırasında hata: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)