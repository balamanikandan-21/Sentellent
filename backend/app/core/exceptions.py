from typing import Any


class AppError(Exception):
    def __init__(
        self,
        status_code: int = 500,
        detail: str = "Internal server error",
        error_code: str = "INTERNAL_ERROR",
        context: dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.context = context or {}
        super().__init__(detail)


class NotFoundError(AppError):
    def __init__(self, entity: str, identifier: str):
        super().__init__(
            status_code=404,
            detail=f"{entity} not found: {identifier}",
            error_code="NOT_FOUND",
            context={"entity": entity, "identifier": identifier},
        )


class ConflictError(AppError):
    def __init__(self, detail: str):
        super().__init__(status_code=409, detail=detail, error_code="CONFLICT")


class UnauthorizedError(AppError):
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=401, detail=detail, error_code="UNAUTHORIZED")


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=403, detail=detail, error_code="FORBIDDEN")


class ValidationError(AppError):
    def __init__(self, detail: str, context: dict[str, Any] | None = None):
        super().__init__(
            status_code=422, detail=detail, error_code="VALIDATION_ERROR", context=context
        )


class ExternalServiceError(AppError):
    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=502,
            detail=f"{service}: {detail}",
            error_code="EXTERNAL_SERVICE_ERROR",
            context={"service": service},
        )
