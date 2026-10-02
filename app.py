"""Entry point for `flask run`, gunicorn (`app:app`) and Vercel."""

from team_builder.app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
