# Cloud-Based Student Learning Management System

A beginner-friendly Flask web application prepared for cloud deployment.

## Local login
- Admin: `admin` / `admin123`
- Student: `student` / `student123`

## Local setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

## Planned AWS deployment
- EC2: application hosting
- RDS MySQL: production database
- S3: learning-material storage
- IAM: permissions and security
- CloudWatch: monitoring and logs
