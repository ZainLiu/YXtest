from flask import Flask, Response, render_template
import cv2

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    camera = cv2.VideoCapture(0)  # 使用摄像头捕获视频
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            # 在这里进行视频处理（如图像处理、人脸识别等）
            # 可以使用 OpenCV 或其他库来处理视频帧

            # 将处理后的视频帧转换为字节流
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # 使用生成器函数返回视频帧
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True)