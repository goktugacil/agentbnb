from flask import Flask, request, jsonify
import pandas as pd
import joblib
import numpy as np
import math

app = Flask(__name__)

GOOGLE_SHEETS_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQtk-7eRprKONHH1LONCddSowpZ85UOnlyYlpA3F5uNiSdU0IgiiacjQuRCY3wGuddbk7ePltMhc00G/pub?gid=1740703900&single=true&output=csv'

model = joblib.load('price_model.pkl')
df = pd.read_csv(GOOGLE_SHEETS_CSV_URL)
model_features = model.get_booster().feature_names

if 'id' not in df.columns:
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'id'}, inplace=True)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
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

        property_data = df[df['id'] == property_id]
        if property_data.empty:
            return jsonify({'error': 'Bu ID ile eşleşen bir kayıt bulunamadı.'}), 404

        features = property_data.drop(columns=['id', 'price'], errors='ignore')
        for col in model_features:
            if col not in features.columns:
                features[col] = 0
        features = features[model_features]
        features = features.apply(pd.to_numeric, errors='coerce')

        prediction = model.predict(features)[0]

        lat, lon = float(property_data['latitude']), float(property_data['longitude'])
        accommodates = int(property_data['accommodates'])

        nearby_properties = df.copy()
        nearby_properties['distance'] = df.apply(lambda row: haversine(lat, lon, row['latitude'], row['longitude']), axis=1)
        competitors = nearby_properties[(nearby_properties['distance'] <= 5) &
                                        (abs(nearby_properties['accommodates'] - accommodates) <= 1)]

        competitor_avg_price = None
        if not competitors.empty:
            competitor_avg_price = round(competitors['price'].mean(), 2)

        minimum_price_suggestion = None
        if competitor_avg_price and prediction > competitor_avg_price:
            minimum_price_suggestion = competitor_avg_price

        review_count = property_data['number_of_reviews'].values[0]
        availability = property_data['availability_365'].values[0]
        host_response_rate = property_data['host_response_rate'].values[0]

        superhost_score = 0
        if host_response_rate:
            superhost_score += (host_response_rate / 100) * 2
        if review_count:
            superhost_score += min(review_count / 100, 2)
        if availability:
            superhost_score += (availability / 365) * 2
        superhost_score = round(superhost_score, 2)

        professional_advice = "Performansınız iyi gözüküyor, devam edin!"
        if competitor_avg_price and prediction > competitor_avg_price:
            professional_advice = "Fiyatınız rakiplerin ortalamasının üzerinde. Erken rezervasyon almak için fiyatı düşürebilirsiniz."

        response = {
            'prediction': round(float(prediction), 2),
            'district': str(property_data['geo_cluster'].values[0]) if 'geo_cluster' in property_data else None,
            'accommodates': accommodates,
            'latitude': lat,
            'longitude': lon,
            'competitor_avg_price': competitor_avg_price,
            'minimum_price_suggestion': minimum_price_suggestion,
            'superhost_score': superhost_score,
            'professional_advice': professional_advice
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': f'İşlem sırasında hata oluştu: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
