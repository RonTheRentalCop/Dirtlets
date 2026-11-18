import socket
import time

from machine import Pin

import config
from camera import Camera, FrameSize, GrabMode, PixelFormat
from wifi import connect_wifi

BOUNDARY = b"dirtletsframe"
INDEX_PAGE = (
    b"<html><body style='background:#111;color:#eee;font-family:sans-serif;text-align:center'>"
    b"<h2>Dirtlets camera</h2><img src='/stream' style='max-width:100%'></body></html>"
)


def start_camera():
    settings = dict(
        frame_size=getattr(FrameSize, config.FRAME_SIZE),
        pixel_format=PixelFormat.JPEG,
        jpeg_quality=config.JPEG_QUALITY,
        grab_mode=GrabMode.LATEST,
    )
    try:
        cam = Camera(fb_count=2, **settings)
    except Exception as error:
        print("Camera with 2 buffers failed (", error, "), trying 1 at QVGA")
        settings["frame_size"] = FrameSize.QVGA
        cam = Camera(fb_count=1, **settings)
    cam.vflip = 1 if config.FLIP_VERTICAL else 0
    cam.hmirror = 1 if config.MIRROR_HORIZONTAL else 0
    return cam


def send_frame(client, frame):
    client.sendall(b"\r\n--" + BOUNDARY + b"\r\nContent-Type: image/jpeg\r\nContent-Length: "
                   + str(len(frame)).encode() + b"\r\n\r\n")
    client.sendall(frame)


def stream(client, cam):
    client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: multipart/x-mixed-replace;boundary="
                   + BOUNDARY + b"\r\nCache-Control: no-cache\r\n\r\n")
    frames, started = 0, time.ticks_ms()
    while True:
        frame = cam.capture()
        if not frame:
            continue
        send_frame(client, frame)
        cam.free_buffer()
        frames += 1
        if frames % 100 == 0:
            seconds = time.ticks_diff(time.ticks_ms(), started) / 1000
            print("Streaming at %.1f fps" % (frames / seconds))


def handle(client, cam):
    request = client.recv(1024)
    if request.startswith(b"GET /stream"):
        print("Stream started")
        stream(client, cam)
    elif request.startswith(b"GET /capture"):
        frame = cam.capture()
        client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: image/jpeg\r\nContent-Length: "
                       + str(len(frame)).encode() + b"\r\n\r\n")
        client.sendall(frame)
        cam.free_buffer()
    else:
        client.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + INDEX_PAGE)


def main():
    Pin(config.FLASH_LED_PIN, Pin.OUT, value=0)
    cam = start_camera()
    station = connect_wifi()

    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(socket.getaddrinfo("0.0.0.0", config.HTTP_PORT)[0][-1])
    server.listen(2)
    ip = station.ifconfig()[0]
    print("Ready. Stream: http://%s:%d/stream  (or http://%s.local:%d/stream)"
          % (ip, config.HTTP_PORT, config.HOSTNAME, config.HTTP_PORT))

    try:
        while True:
            client, address = server.accept()
            client.settimeout(config.SEND_TIMEOUT_S)
            try:
                handle(client, cam)
            except OSError as error:
                print("Viewer", address[0], "disconnected:", error)
            finally:
                client.close()
    except KeyboardInterrupt:
        print("Stopping camera")
    finally:
        server.close()
        cam.deinit()


main()
