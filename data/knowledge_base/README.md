# Medical RAG Knowledge Base

This folder contains sample Markdown documents for the FastAPI + WebSocket + Groq medical RAG chatbot.

## Files

- `00_medical_safety_and_emergency_red_flags.md`
- `01_diabetes_overview.md`
- `02_hypertension_and_blood_pressure.md`
- `03_fever_cold_flu_and_respiratory_symptoms.md`
- `04_dehydration_diarrhoea_and_vomiting.md`
- `05_headache_and_migraine_safety.md`
- `06_medication_safety.md`
- `07_rag_chatbot_response_policy.md`

## How to use

Upload these files from the chatbot admin/upload interface, or copy them into the project's document folder and call the ingestion endpoint.

Example target folder:

```text
medical-rag-chatbot/
└── data/
    └── documents/
```

## Important

These files are intentionally written as educational knowledge-base content. They must not be used as a substitute for professional medical diagnosis, emergency care, or medication prescribing.
