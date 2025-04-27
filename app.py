{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "deab28df-88e8-4d6f-ab9d-081769be4597",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Collecting flask\n",
      "  Downloading flask-3.1.0-py3-none-any.whl.metadata (2.7 kB)\n",
      "Requirement already satisfied: requests in ./Library/jupyterlab-desktop/jlab_server/lib/python3.12/site-packages (2.32.3)\n",
      "Collecting Werkzeug>=3.1 (from flask)\n",
      "  Downloading werkzeug-3.1.3-py3-none-any.whl.metadata (3.7 kB)\n",
      "Requirement already satisfied: Jinja2>=3.1.2 in ./Library/jupyterlab-desktop/jlab_server/lib/python3.12/site-packages (from flask) (3.1.4)\n",
      "Collecting itsdangerous>=2.2 (from flask)\n",
      "  Using cached itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)\n",
      "Collecting click>=8.1.3 (from flask)\n",
      "  Using cached click-8.1.8-py3-none-any.whl.metadata (2.3 kB)\n",
      "Collecting blinker>=1.9 (from flask)\n",
      "  Using cached blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)\n",
      "Requirement already satisfied: charset-normalizer<4,>=2 in ./Library/jupyterlab-desktop/jlab_server/lib/python3.12/site-packages (from requests) (3.3.2)\n",
      "Requirement already satisfied: idna<4,>=2.5 in ./Library/jupyterlab-desktop/jlab_server/lib/python3.12/site-packages (from requests) (3.8)\n",
      "Requirement already satisfied: urllib3<3,>=1.21.1 in ./Library/jupyterlab-desktop/jlab_server/lib/python3.12/site-packages (from requests) (2.2.2)\n",
      "Requirement already satisfied: certifi>=2017.4.17 in ./Library/jupyterlab-desktop/jlab_server/lib/python3.12/site-packages (from requests) (2024.7.4)\n",
      "Requirement already satisfied: MarkupSafe>=2.0 in ./Library/jupyterlab-desktop/jlab_server/lib/python3.12/site-packages (from Jinja2>=3.1.2->flask) (2.1.5)\n",
      "Downloading flask-3.1.0-py3-none-any.whl (102 kB)\n",
      "Using cached blinker-1.9.0-py3-none-any.whl (8.5 kB)\n",
      "Using cached click-8.1.8-py3-none-any.whl (98 kB)\n",
      "Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)\n",
      "Downloading werkzeug-3.1.3-py3-none-any.whl (224 kB)\n",
      "Installing collected packages: Werkzeug, itsdangerous, click, blinker, flask\n",
      "Successfully installed Werkzeug-3.1.3 blinker-1.9.0 click-8.1.8 flask-3.1.0 itsdangerous-2.2.0\n",
      "Note: you may need to restart the kernel to use updated packages.\n"
     ]
    }
   ],
   "source": [
    "pip install flask requests"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "4813e88e-1196-4f4e-8d10-50b518c47581",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      " * Serving Flask app '__main__'\n",
      " * Debug mode: off\n"
     ]
    },
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.\n",
      " * Running on all addresses (0.0.0.0)\n",
      " * Running on http://127.0.0.1:5001\n",
      " * Running on http://192.168.1.116:5001\n",
      "Press CTRL+C to quit\n"
     ]
    }
   ],
   "source": [
    "from flask import Flask, request, jsonify\n",
    "import requests\n",
    "\n",
    "app = Flask(__name__)\n",
    "\n",
    "AIRTABLE_API_KEY = 'patKSNNIqaRvCSVQd.bfe0ec81c349def3482c6c527f255e76ee121d85e9c3850b5b2b7c06cc5bbc4f'\n",
    "AIRTABLE_BASE_ID = 'appmdEYMPfmYmjqTl'\n",
    "AIRTABLE_TABLE_NAME = 'Sayfa1'\n",
    "\n",
    "@app.route('/get_property', methods=['GET'])\n",
    "def get_property():\n",
    "    property_id = request.args.get('id')\n",
    "\n",
    "    if not property_id:\n",
    "        return jsonify({\"error\": \"ID parametresi eksik\"}), 400\n",
    "\n",
    "    url = f\"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}\"\n",
    "    headers = {\n",
    "        \"Authorization\": f\"Bearer {AIRTABLE_API_KEY}\"\n",
    "    }\n",
    "    params = {\n",
    "        \"filterByFormula\": f\"{{id}}='{property_id}'\"\n",
    "    }\n",
    "\n",
    "    response = requests.get(url, headers=headers, params=params)\n",
    "\n",
    "    if response.status_code != 200:\n",
    "        return jsonify({\"error\": f\"Airtable Hatası: {response.status_code}\", \"details\": response.text}), 500\n",
    "\n",
    "    airtable_data = response.json()\n",
    "\n",
    "    if len(airtable_data.get('records', [])) == 0:\n",
    "        return jsonify({\"error\": \"Bu ID ile eşleşen bir ev bulunamadı.\"}), 404\n",
    "\n",
    "    fields = airtable_data['records'][0]['fields']\n",
    "\n",
    "    return jsonify({\n",
    "        \"district\": fields.get(\"district\"),\n",
    "        \"accommodates\": fields.get(\"accommodates\"),\n",
    "        \"bedrooms\": fields.get(\"bedrooms\"),\n",
    "        \"bathrooms\": fields.get(\"bathrooms\"),\n",
    "        \"predicted_price\": fields.get(\"predicted_price\"),\n",
    "        \"predicted_superhost\": fields.get(\"predicted_superhost\")\n",
    "    })\n",
    "\n",
    "if __name__ == '__main__':\n",
    "    app.run(host='0.0.0.0', port=5001)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "0892a6dc-4f6a-4d4c-9831-4f8a4b36d146",
   "metadata": {},
   "outputs": [],
   "source": [
    "print(os.path.abspath(__file__))"
   ]
  },
  {
   "cell_type": "code",
   "id": "5680e32e-c43c-4afa-84bb-66245ef99102",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.5"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
