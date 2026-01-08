import os


class Settings:
    """
    Settings class to manage application configuration.
    Retrieves configuration values from environment variables.
    Provides methods for debelop database URLs.
    """

    @staticmethod
    def get_db_url() -> str:
        """
        Constructs the database URL from environment variables.
        """
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        db_name = os.getenv("DB_NAME")

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"