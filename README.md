\# VerifyHire — AI-Powered Video Hiring Platform



> Published Research · IJEDR Vol. 14, Issue 2, April 2026 (ISSN: 2321-9939)



\## Overview



VerifyHire is a full-stack AI hiring platform enabling blue-collar workers to submit video resumes instead of traditional text CVs. Employers review AI-scored candidates ranked by skill match and identity verification.



\## AI Pipeline



| Stage | Component | Detail |

|-------|-----------|--------|

| 1 | Face Detection | YOLOv8 (0.965 confidence) |

| 2 | Identity Verification | DeepFace ArcFace |

| 3 | Speech Transcription | Faster-Whisper |

| 4 | Skill Extraction | spaCy NER |

| 5 | Job Matching | SentenceBERT (70% SBERT + 30% Jaccard) |



\## Tech Stack



| Layer | Technology |

|-------|-----------|

| Frontend | Next.js 14 |

| Backend | FastAPI + PostgreSQL |

| AI/ML | YOLOv8 · DeepFace · Whisper · spaCy · SBERT |

| Auth | JWT (Worker / Employer / Admin roles) |



\## Research Publication



Co-authored and published in the \*\*International Journal of Engineering Development and Research (IJEDR)\*\*, Vol. 14, Issue 2, April 2026, ISSN 2321-9939.



\## Setup



```bash

cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload

```



\## Author



\*\*Varshitha Chinta\*\*

B.Tech CSE, Andhra University College of Engineering for Women

ML Intern @ Kalam Dream Labs | Published Researcher | Cognizant × Aston Martin F1 Ideathon Winner



\- 🔗 \[GitHub](https://github.com/varshithachinta)

\- 💼 \[LinkedIn](https://linkedin.com/in/varshithachinta)

