# AWS Setup Guide — Driving Coach LLM

This guide describes how to set up the application on AWS EC2.

---

## 1. Launch EC2 Instance

* Instance Type: t3.micro
* OS: Ubuntu
* Enable:

  * IAM role with S3 + SSM access
* Configure Security Group:

| Port | Purpose               |
| ---- | --------------------- |
| 7860 | Gradio UI             |
| 8000 | FastAPI (optional)    |
| 8080 | LLM server            |

---

## 2. Connect to Instance

Using AWS Systems Manager (SSM) or SSH:

```bash
sudo su - ubuntu
```

---

## 3. Install Dependencies

```bash
sudo apt update
sudo apt install -y git cmake python3-venv python3-pip
```

---

## 4. Clone Repository

```bash
git clone <repository_link>
cd driving-coach-app/app
```

---

## 5. Setup Python Environment

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install requests
```

---

## 6. Setup llama.cpp

```bash
cd ~

git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

mkdir build && cd build
cmake ..
cmake --build . --config Release
```

---

## 7. Download Model from S3

```bash
aws s3 cp s3://<your-bucket>/driving-coach-f16.gguf /home/ubuntu/
```

---

## 8. Run LLM Server

```bash
cd ~/llama.cpp/build/bin

./llama-server \
  -m /home/ubuntu/driving-coach-f16.gguf \
  --port 8080 \
  --ctx-size 1024
```

---

## 9. Run Application

```bash
cd ~/driving-coach-app/app
source venv/bin/activate

python main.py
```

---

## 10. Logging Setup (Optional)

```bash
mkdir -p ~/logs

./llama-server ... 2>&1 | tee -a ~/logs/llama.log
python main.py 2>&1 | tee -a ~/logs/app.log
```

---

## 11. Monitoring (CloudWatch)

* Install CloudWatch Agent
* Configure log path:

```text
/home/ubuntu/logs/*.log
```

---

## 12. Access Application

```text
http://<EC2_PUBLIC_IP>:7860
```

---

## 13. Notes

* Ensure sufficient memory (reduce context size if needed)
* Model must exist locally before starting server
* Keep ports secured in production

---

## 14. Cleanup

Stop instance when not in use to avoid charges.
