from enum import StrEnum


class LLMClientType(StrEnum):
    OPENAI = "OPEN_AI"
    ANTHROPIC = "ANTHROPIC"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


class Role(StrEnum):
    ROLE = "role"
    SYSTEM = "system"
    USER = "user"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


class ContentType(StrEnum):
    CONTENT = "content"
    TEXT = "text"
    TYPE = "type"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)


class LLMModel(StrEnum):
    GPT4o = "gpt-4o"
    GPT4oMini = "gpt-4o-mini"
    Claude3_5Sonnet = "claude-3-5-sonnet-20240620"

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self.value)
