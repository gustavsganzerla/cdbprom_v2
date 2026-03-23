import sys
import argparse
from Bio import SeqIO
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForMaskedLM
import torch
import csv

##functions to encode the inputs (from the flask app)
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



model_dir = 'ft_model_files'

tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=False)
model = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
model.eval()


def main():
    parser = argparse.ArgumentParser(description="Run CDBProm's predictor locally")
    parser.add_argument("input_file", help="Path to te input file")
    parser.add_argument(
        "-o", "--output_file", help="Optional: path to save results", default=None
    )
    parser.add_argument(
        "-s", "--step_size", help="Optional: step size to generate subsequences in input sequences with length>60. Default = 10."
    )

    args = parser.parse_args()

    output = []
    with open(args.input_file, 'r') as f:
        for record in SeqIO.parse(f, 'fasta'):
            seq = str(record.seq)
            id = str(record.id)

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
            
            elif len(seq) > 60:
                windows = []
                window_size = 60

                if args.step_size:
                    step_size = int(args.step_size)
                else:
                    step_size = 10

                for i in range(0, len(seq)-window_size+1, step_size):
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
                            'Sequence':window
                    })
            
    if args.output_file:
        keys = output[0].keys()
        with open(args.output_file, 'w', newline="") as out:
            writer = csv.DictWriter(out, fieldnames=keys)
            writer.writeheader()
            writer.writerows(output)


    print(output)
        
            

            



if __name__ == '__main__':
    main()