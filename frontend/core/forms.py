from django import forms


class QueryForm(forms.Form):
    gene_name = forms.CharField(label="Gene name", max_length=100, required=False)
    annotation = forms.CharField(label="Annotation", max_length=100, required=False)
    ncbi_id = forms.CharField(label="NCBI ID", max_length=100, required=False)

class InputForm(forms.Form):
    sequence_text = forms.CharField(widget=forms.Textarea(attrs={"rows":10,
                                                               "cols":60,
                                                               "placeholder": "Promoter sequences in FASTA format"}),
    required=False)

    uploaded_file = forms.FileField(required=False)