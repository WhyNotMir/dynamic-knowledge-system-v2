from sqlalchemy.types import UserDefinedType


class Vector(UserDefinedType):
    cache_ok = True

    def get_col_spec(self, **kw) -> str:
        return "vector"

    def bind_processor(self, dialect):
        def process(value):
            if value is None:
                return None
            return "[" + ",".join(str(float(item)) for item in value) + "]"

        return process

    def result_processor(self, dialect, coltype):
        def process(value):
            if value is None or isinstance(value, list):
                return value
            text = str(value).strip()
            if text.startswith("[") and text.endswith("]"):
                text = text[1:-1]
            if not text:
                return []
            return [float(item) for item in text.split(",")]

        return process
