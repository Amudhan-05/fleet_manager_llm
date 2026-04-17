# User Manual

## Overview

This application analyzes driving session data and generates personalized coaching feedback using a fine-tuned LLM deployed on AWS EC2. The system combines sensor data processing with natural language generation to provide actionable insights for drivers and fleet managers.

---

## Prerequisites

* AWS EC2 instance (Ubuntu recommended)
* Python 3.10+
* Git installed
* AWS CLI configured (for S3 access)
* Internet access

---

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-link>
cd driving-coach-app/app
```

---

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install requests
```

---

## Model Setup

Download the GGUF model from S3:

```bash
aws s3 cp s3://<your-bucket>/driving-coach-f16.gguf /home/ubuntu/
```

---

## Running the System

### Step 1 — Start LLM Server

```bash
cd ~/llama.cpp/build/bin

./llama-server \
  -m /home/ubuntu/driving-coach-f16.gguf \
  --port 8080 \
  --ctx-size 1024
```

---

### Step 2 — Start Application

```bash
cd ~/driving-coach-app/app
source venv/bin/activate

python main.py
```

---

## Access the Application

* **Gradio UI:**
  http://<EC2_PUBLIC_IP>:7860

* **Swagger UI (optional API testing):**
  http://<EC2_PUBLIC_IP>:8000/docs

---

## Usage

1. Open the Gradio interface in your browser
2. Select a driver and trip
3. Trigger analysis
4. View generated coaching feedback

Fleet managers can access aggregated insights via the coach interface.

---

## Troubleshooting

### Application not accessible

* Ensure ports **7860 / 8000** are open in EC2 security group

### LLM crashes

* Reduce context size:

```bash
--ctx-size 1024
```

### Slow responses

* Reduce token limits in backend
* Use smaller model if needed

### S3 download fails

* Check IAM role permissions
* Verify AWS CLI configuration

---

## Notes

* Ensure the LLM server is running before starting the app
* Do not commit `.env` files or credentials
* Model file should remain outside the repo

---

## Project Structure (Simplified)

```text
driving-coach-app/
└── app/
    ├── backend/
    ├── ui/
    ├── data/
    ├── main.py
    └── requirements.txt
```

---

## Future Improvements

* Add caching for faster responses
* Enable streaming output
* Containerize using Docker
* Scale using GPU instances
