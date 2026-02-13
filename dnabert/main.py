from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForMaskedLM
import torch
import logging
from flask_cors import CORS
from functools import wraps
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = 'MY_KEY'

def seq_to_kmers(seq, k=6):
    seq = seq.upper().replace("N", "")
    if len(seq) < k:
        return ""
    return " ".join(seq[i:i+k] for i in range(len(seq) - k + 1))

def predict_sequence(seq):
    kmers = seq_to_kmers(seq)
    if not kmers:
        kmers = tokenizer.pad_token

    enc = tokenizer(
        kmers,
        padding="max_length",
        truncation=True,
        max_length=60,
        return_tensors="pt"
    )

    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.no_grad():
        logits = model(**enc).logits
        probs = torch.softmax(logits, dim=-1)
    return probs.cpu().numpy()[0]




app = Flask(__name__)
CORS(app, origins=["http://localhost:8000"],
     allow_headers=["Content-Type", "X-API-KEY"])

model_dir = 'ft_model_files'

tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()


def limit_to_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_provided_key = request.headers.get('X-API-KEY')
        
        if not user_provided_key or user_provided_key != API_KEY:
            return jsonify({"error": "Invalid or missing API key"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

###API endpoint
@app.route("/predict", methods=["POST"])
@app.route("/predict/", methods=["POST"])
@limit_to_key
def predict():
    data = request.get_json()
    sequences = data['sequences']
    output = []


    if len(sequences) > 3:
        output.append({
            'Message':f"Too many input sequences (n={len(sequences)})\nThe maximum number of input sequences supported is 100."
        })
    
    elif len(sequences) <= 3:
        for item in sequences:
            seq = item.get('seq')
            id = item.get('id')

            if len(seq) == 60:
                probs = predict_sequence(seq)

                output.append({
                    'id':id,
                    'Coordinates':f'1 - {len(seq)}',
                    'Probability non-promoter':f'{float(probs[0]*100):.2f}%',
                    'Probability promoter':f'{float(probs[1]*100):.2f}%',
                    'Predicted class':'Promoter' if float(probs[1])>float(probs[0]) else 'Non-promoter',
                    'Message': 'Success',
                    'Sequence':seq
                })
            elif len(seq) > 60 and len(seq) <= 1000:
                windows = []
                step = 10
                window_size = 60

                for i in range(0, len(seq)-window_size+1, step):
                    windows.append(seq[i:i+window_size])
                    window = (seq[i:i+window_size])
                    probs = predict_sequence(window)

                    output.append({
                            'id':id,
                            'Coordinates':f'{i} - {i+window_size}',
                            'Probability non-promoter':f'{float(probs[0]*100):.2f}%',
                            'Probability promoter':f'{float(probs[1]*100):.2f}%',
                            'Predicted class':'Promoter' if float(probs[1])>float(probs[0]) else 'Non-promoter',
                            'Message': 'Success',
                            'Sequence':seq
                    })
            
            elif len(seq)>1000:
                output.append({
                            'id':id,
                            'Coordinates':'NA',
                            'Probability non-promoter':'NA',
                            'Probability promoter':'NA',
                            'Predicted class':'NA',
                            'Message':'Error.\nSequence with length greater than 1000.\nThe maximum length per sequence is 1000.',
                            'Sequence':seq
                    })
            else:
                output.append({
                            'id':id,
                            'Coordinates':'NA',
                            'Probability non-promoter':'NA',
                            'Probability promoter':'NA',
                            'Predicted class':'NA',
                            'Message':'Input sequence(s) too short. The minimum length is 60.',
                            'Sequence':seq
                    })
    
    
    return jsonify({"output": output})


# --------- Run server ---------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
