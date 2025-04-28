from flask import Flask, request, jsonify
import pandas as pd
import joblib

app = Flask(__name__)

GOOGLE_SHEETS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQtk-7eRprKONHH1LONCddSowpZ85UOnlyYlpA3F5uNiSdU0IgiiacjQuRCY3wGuddbk7ePltMhc00G/pub?output=csv"

# Model yükle
model = joblib.load('price_model.pkl')

# Veriyi yükle
df = pd.read_csv(GOOGLE_SHEETS_CSV_URL, low_memory=False)

# Modelin beklediği feature listesi
model_features = model.get_booster().feature_names

# Eğer id yoksa oluştur
if 'id' not in df.columns:
    df.reset_index(inplace=True)
    df.rename(columns={'index': 'id'}, inplace=True)

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

        return jsonify({
            'prediction': round(float(prediction), 2),
            'district': str(prop['geo_cluster'].iloc[0]) if 'geo_cluster' in prop else None,
            'accommodates': int(prop['accommodates'].iloc[0]) if 'accommodates' in prop else None,
            'professional_advice': "Performansınız iyi gözüküyor, devam edin!"
        })

    except Exception as e:
        return jsonify({'error': f'İşlem sırasında hata: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)