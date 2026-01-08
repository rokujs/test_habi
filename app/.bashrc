export PS1="[fastapi-docker] \u@\h:\w$"
export PATH="$PATH:/root/.local/bin/"

# ALIAS
alias shell="source .venv/bin/activate"
alias migrate="alembic upgrade head"
alias makemigrations="alembic revision --autogenerate -m"