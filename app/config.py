from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")
    api_key: str = Field(default="change-me", alias="API_KEY")
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-3-5-sonnet-latest", alias="ANTHROPIC_MODEL")

    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")

    ip_hash_salt: str = Field(default="", alias="IP_HASH_SALT")
    chat_memory_messages: int = Field(default=10, alias="CHAT_MEMORY_MESSAGES")

    public_api_base: str = Field(default="", alias="PUBLIC_API_BASE")
    public_widget_src: str = Field(default="https://dental-bot-widget.vercel.app/widget.js", alias="PUBLIC_WIDGET_SRC")
    redis_url: str = Field(default="", alias="REDIS_URL")
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    email_from: str = Field(default="no-reply@example.com", alias="EMAIL_FROM")


    def origins_list(self) -> List[str]:
        if self.allowed_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
    
settings = Settings()
