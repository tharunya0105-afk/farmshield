.PHONY: install run dev test clean reset

install:
	pip install -r requirements.txt

run dev:
	cd backend && python -m uvicorn main:app --reload --port 8000 --host 127.0.0.1

test:
	python -m pytest tests/ -v || python test_e2e.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f backend/farmshield.db

reset:
	curl -X POST http://localhost:8000/api/demo/reset
