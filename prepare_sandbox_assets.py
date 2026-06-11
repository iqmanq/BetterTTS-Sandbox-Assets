import os
import requests
import base64
import json

output_dir = "/home/iqraa/dev/BetterTTS-Sandbox-Assets"
model_dir = os.path.join(output_dir, "model")
voices_dir = os.path.join(output_dir, "voices")

os.makedirs(model_dir, exist_ok=True)
os.makedirs(voices_dir, exist_ok=True)

# 1. Download Model
model_url = "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/onnx/model_q4.onnx"
model_path = os.path.join(output_dir, "model_q4.onnx")

print("Downloading model_q4.onnx...")
r = requests.get(model_url)
r.raise_for_status()
with open(model_path, "wb") as f:
    f.write(r.content)
print(f"Model downloaded. Size: {len(r.content)} bytes")

# Encode and chunk model
with open(model_path, "rb") as f:
    b64_data = base64.b64encode(f.read()).decode("utf-8")

chunk_size = 1000000 # 1MB chunks
chunks = [b64_data[i:i+chunk_size] for i in range(0, len(b64_data), chunk_size)]

print(f"Splitting model into {len(chunks)} JS chunks...")
for idx, chunk in enumerate(chunks):
    chunk_file = os.path.join(model_dir, f"part_{idx}.js")
    with open(chunk_file, "w", encoding="utf-8") as f:
        # Wrap chunk in a global array index
        f.write(f'window.KOKORO_MODEL_PARTS = window.KOKORO_MODEL_PARTS || [];\n')
        f.write(f'window.KOKORO_MODEL_PARTS[{idx}] = "{chunk}";\n')
    print(f"  Wrote {chunk_file}")

# 2. Download and encode voices
voices = [
    "af_alloy", "af_bella", "af_heart", "af_sarah", 
    "am_adam", "am_echo", "am_fenrir", 
    "bf_emma", "bf_isabella", "bm_daniel", "bm_lewis"
]

for voice in voices:
    voice_url = f"https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main/voices/{voice}.bin"
    print(f"Downloading voice {voice}.bin...")
    r = requests.get(voice_url)
    r.raise_for_status()
    
    # Encode voice
    v_b64 = base64.b64encode(r.content).decode("utf-8")
    
    voice_file = os.path.join(voices_dir, f"voice_{voice}.js")
    with open(voice_file, "w", encoding="utf-8") as f:
        # Wrap voice in a global mapping dictionary
        f.write(f'window.KOKORO_VOICES = window.KOKORO_VOICES || {{}};\n')
        f.write(f'window.KOKORO_VOICES["{voice}"] = "{v_b64}";\n')
    print(f"  Wrote {voice_file}")

# 3. Download and encode WASM files for ONNX Runtime 1.20.0
wasm_dir = os.path.join(output_dir, "wasm")
os.makedirs(wasm_dir, exist_ok=True)

wasm_files = {
    "ort-wasm-simd.wasm": "wasm_simd.js",
    "ort-wasm.wasm": "wasm_default.js"
}

for wasm_name, js_name in wasm_files.items():
    wasm_url = f"https://cdn.jsdelivr.net/npm/onnxruntime-web@1.20.0/dist/{wasm_name}"
    print(f"Downloading {wasm_name}...")
    r = requests.get(wasm_url)
    r.raise_for_status()
    
    w_b64 = base64.b64encode(r.content).decode("utf-8")
    
    js_path = os.path.join(wasm_dir, js_name)
    var_name = "KOKORO_WASM_SIMD_B64" if "simd" in wasm_name else "KOKORO_WASM_DEFAULT_B64"
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(f'window.{var_name} = "{w_b64}";\n')
    print(f"  Wrote {js_path}")

print("Clean up original binary files to keep repository clean...")
if os.path.exists(model_path):
    os.remove(model_path)

print("SUCCESS: All sandbox assets prepared successfully!")
