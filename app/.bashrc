export PS1="[fastapi-docker] \u@\h:\w$"
export PATH="$PATH:/root/.local/bin/"

# ALIAS
alias test="pytest tests"
alias runserver="uv run fastapi dev main.py --port 8000 --host 0.0.0.0"
alias shell="source .venv/bin/activate"
alias migrate="alembic upgrade head"
alias makemigrations="alembic revision --autogenerate -m"