import os
import subprocess
import time
import threading
import queue
import logging
from flask import Flask, render_template, request, Response, send_from_directory, abort
from flask import Flask, Response, request

app = Flask(__name__, template_folder='/home/nathan/webfiles_static/html/tidal-dl', static_folder='/home/nathan/webfiles_static/html/tidal-dl')

# Configure logging (info and error only)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration via environment
TIDAL_DL_BIN = os.environ.get('TIDAL_DL_BIN', '/home/nathan/.local/bin/tidal-dl-ng')
DOWNLOAD_TIMEOUT = int(os.environ.get('DOWNLOAD_TIMEOUT', '0'))  # seconds; 0 = no timeout
DOWNLOAD_TOKEN = os.environ.get('DOWNLOAD_TOKEN')  # optional: if set, require header X-Download-Token

# Store output in a bounded queue for streaming (prevents unbounded memory growth)
output_queue = queue.Queue(maxsize=2000)
# current_process is protected by process_lock
current_process = None
process_lock = threading.Lock()

# Validate binary at startup (log warnings but do not crash)
if not os.path.isfile(TIDAL_DL_BIN) or not os.access(TIDAL_DL_BIN, os.X_OK):
    logging.warning(f"TIDAL_DL_BIN '{TIDAL_DL_BIN}' is not present or not executable. Please set env TIDAL_DL_BIN to a valid binary path.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tidal-dl/')
def index_tidal():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico')

@app.route('/download', methods=['POST'])
@app.route('/tidal-dl/download', methods=['POST'])
def download():
    global current_process
    # optional token auth: if DOWNLOAD_TOKEN is set, require header
    if DOWNLOAD_TOKEN:
        token = request.headers.get('X-Download-Token')
        if token != DOWNLOAD_TOKEN:
            logging.warning('Unauthorized download attempt (invalid/missing token)')
            return ({"error": "Unauthorized"}, 401)
    url = request.form.get('url')
    if not url:
        logging.error("No URL provided")
        return {"error": "No URL provided"}, 400

    def run_download():
        global current_process
        try:
            logging.info(f"Starting download for URL: {url}")
            # Clear previous output (non-atomic but reasonable)
            try:
                while True:
                    output_queue.get_nowait()
            except queue.Empty:
                pass

            # Run tidal-dl-ng
            command = [TIDAL_DL_BIN, 'dl', url]
            process = None
            with process_lock:
                # Start process and register it as the current process
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
                current_process = process

            # Read lines robustly
            try:
                for line in iter(process.stdout.readline, ''):
                    if line == '':
                        break
                    # best-effort non-blocking put: drop oldest if full
                    try:
                        output_queue.put(line, timeout=0.5)
                    except queue.Full:
                        try:
                            _ = output_queue.get_nowait()
                        except queue.Empty:
                            pass
                        try:
                            output_queue.put_nowait(line)
                        except queue.Full:
                            # if still full, discard
                            pass

                # Wait for completion (configurable)
                if DOWNLOAD_TIMEOUT and DOWNLOAD_TIMEOUT > 0:
                    try:
                        process.wait(timeout=DOWNLOAD_TIMEOUT)
                    except subprocess.TimeoutExpired:
                        output_queue.put("Error: Command timed out")
                        logging.error("Command timed out")
                        # attempt graceful termination below
                else:
                    process.wait()

                if process.returncode == 0:
                    output_queue.put("Download completed successfully")
                    logging.info("Download completed successfully")
                else:
                    output_queue.put(f"Error: Download failed (exit {process.returncode})")
                    logging.error(f"Download failed (exit {process.returncode})")
            finally:
                # Ensure process pipe is closed
                try:
                    if process and process.stdout:
                        process.stdout.close()
                except Exception:
                    pass
                with process_lock:
                    if current_process is process:
                        current_process = None
        except subprocess.TimeoutExpired:
            output_queue.put("Error: Command timed out")
            logging.error("Command timed out")
            # Attempt graceful termination
            try:
                if process:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            except Exception as e:
                logging.error(f"Error terminating process after timeout: {e}")
            with process_lock:
                if current_process is process:
                    current_process = None
        except Exception as e:
            output_queue.put(f"Error: {str(e)}")
            logging.error(f"Error in download: {str(e)}")
            with process_lock:
                if current_process is process:
                    current_process = None

    # Stop any existing process (safely)
    with process_lock:
        if current_process:
            try:
                current_process.terminate()
                try:
                    current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    current_process.kill()
                    current_process.wait()
            except Exception as e:
                logging.error(f"Error stopping previous process: {e}")
            current_process = None
    # Start new download
    threading.Thread(target=run_download, daemon=True).start()
    return {"message": "Download started"}, 200

@app.route('/tidal-dl/stop', methods=['POST'])
def stop():
    global current_process
    with process_lock:
        if current_process:
            try:
                current_process.terminate()
                try:
                    current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    current_process.kill()
                    current_process.wait()
            except Exception as e:
                logging.error(f"Error stopping process: {e}")
            current_process = None
            output_queue.put("Download stopped")
            logging.info("Download stopped")
            return {"message": "Download stopped"}, 200
    return {"message": "No download running"}, 200

@app.route('/tidal-dl/stream', methods=['GET'])
@app.route('/stream', methods=['GET'])
def stream():
    def generate():
        try:
            yield ': keep-alive\n\n'
            while True:
                try:
                    line = output_queue.get(timeout=0.5)
                    yield f"data: {line}\n\n"
                except queue.Empty:
                    yield ': keep-alive\n\n'
                    time.sleep(0.5)
        except GeneratorExit:
            logging.info("SSE stream closed")

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive'}
    )

if __name__ == '__main__':
    app.run(host='192.168.4.113', port=5050, debug=False)
