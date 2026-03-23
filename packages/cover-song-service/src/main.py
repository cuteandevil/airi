import subprocess
import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response
import uvicorn

app = FastAPI(title="AI Cover Song Service")

AI_COVERS_ROOT = r"D:\AI_covers"
AI_COVERS_MAIN = os.path.join(AI_COVERS_ROOT, "main.py")

@app.post("/cover")
async def create_cover(
    file: UploadFile = File(...),
    target_speaker: str = Form(...),
    output_format: str = Form("wav")
):
    # Save uploaded file to temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_in:
        content = await file.read()
        tmp_in.write(content)
        input_path = tmp_in.name

    # Prepare output path
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_format}") as tmp_out:
        output_path = tmp_out.name

    # Build command
    cmd = [
        "python",
        AI_COVERS_MAIN,
        "--input", input_path,
        "--target_speaker", target_speaker,
        "--output", output_path,
        "--device", "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    ]

    # Run AI_covers
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return Response(content=f"AI Covers error: {result.stderr}", status_code=500)
    except subprocess.TimeoutExpired:
        return Response(content="AI Covers processing timed out", status_code=504)
    finally:
        # Clean up input temp file
        try:
            os.remove(input_path)
        except OSError:
            pass

    # Read output file
    try:
        with open(output_path, "rb") as f:
            data = f.read()
    except Exception as e:
        return Response(content=f"Failed to read output: {e}", status_code=500)
    finally:
        try:
            os.remove(output_path)
        except OSError:
            pass

    # Return audio
    media_type = f"audio/{output_format}"
    return Response(content=data, media_type=media_type)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
