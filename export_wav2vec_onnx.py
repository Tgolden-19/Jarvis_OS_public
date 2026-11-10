import torch
import onnx
from transformers import Wav2Vec2ForCTC, Wav2Vec2Config
import os

model_name = "facebook/wav2vec2-base-960h"
output_onnx_path = "models/wav2vec2_960h.onnx"
opset_version = 11

print(f"Loading model: {model_name}")
# We use Wav2Vec2ForCTC as it includes the classification head necessary for ASR
model = Wav2Vec2ForCTC.from_pretrained(model_name)
model.eval()

# Define dummy input matching the expected input format for Wav2Vec2
# Input is a 1-second audio snippet sampled at 16kHz (batch size 1)
dummy_input_values = torch.randn(1, 16000)

print(f"Starting ONNX export to {output_onnx_path} with opset {opset_version}")

# ... (lines 1-21 remain the same) ...

# Export the model using a TUPLE for inputs instead of a dictionary
torch.onnx.export(
    model,
    # Pass a tuple containing ONLY the input tensor
    (dummy_input_values,), 
    output_onnx_path,
    opset_version=opset_version,
    input_names=['input_values'],
    output_names=['logits'],
    dynamic_axes={
        'input_values': {1: 'sequence_length'}, # Allows variable length audio inputs
        'logits': {1: 'sequence_length_out'}
    },
    verbose=False
)

print(f"Successfully exported model to {output_onnx_path}")

# ... (verification code remains the same) ...


# Optional: Verify the ONNX model structure
try:
    onnx_model = onnx.load(output_onnx_path)
    onnx.checker.check_model(onnx_model)
    print("ONNX model verification successful.")
except onnx.checker.ValidationError as e:
    print(f"ONNX model verification failed: {e}")

