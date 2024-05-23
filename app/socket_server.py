from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

from src.server import Server
from src.asr.asr_factory import ASRFactory
from src.vad.vad_factory import VADFactory

import os

app = FastAPI()

# HTML content to serve for the main page, including WebSocket JS code
html = html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Stream Audio via WebSocket</title>
</head>
<body>
    <h1>Stream Audio to FastAPI Server</h1>
    <button id="startButton">Start Streaming</button>
    <button id="stopButton">Stop Streaming</button>
    <div id="transcription">Transcriptions appear here...</div> <!-- Display area for transcriptions -->
    <script>
        const ws = new WebSocket('ws://localhost:8000/ws');
        let mediaRecorder;
        const transcriptionDisplay = document.getElementById('transcription'); // Get the transcription display element

        async function startStreaming() {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = function (event) {
                if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                    ws.send(event.data);
                }
            };
            mediaRecorder.start(2000); // Collect 1000ms of audio before sending
        }

        document.getElementById('startButton').onclick = () => {
            startStreaming();
        };

        document.getElementById('stopButton').onclick = () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
        };

        ws.onmessage = function(event) {
            console.log('Received:', event.data);
            transcriptionDisplay.innerHTML += '<p>' + event.data + '</p>'; // Append received text to the display area
        };
    </script>
</body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    vad_args={}
    vad_args['auth_token']=os.getenv('HF_TOKEN')

    asr_args={"model_size": "large-v3"}



    vad_pipeline = VADFactory.create_vad_pipeline("pyannote", **vad_args)
    asr_pipeline = ASRFactory.create_asr_pipeline("faster_whisper", **asr_args)

    server = Server(vad_pipeline, asr_pipeline,sampling_rate=16000, samples_width=2)

    await server.handle_websocket(websocket)

    # await websocket.accept()
    # try:
    #     while True:
    #         # Receive audio data as bytes
    #         audio_data = await websocket.receive_bytes()
    #         print("Received audio data")
            
    #         # You can process the audio data here if needed

    #         # Echo the audio data back to the client
    #         await websocket.send_bytes(audio_data)
    # except Exception as e:
    #     print('WebSocket error:', e)
    # finally:
    #     await websocket.close()
