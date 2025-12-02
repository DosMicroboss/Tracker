from core.functional import either
from core.domain import Task

class TaskService:
    def __init__(self, validators: list):
        self.validators = validators

    def create_task(self, t: Task) -> either[dict, Task]:
        errors = {}

        for v in self.validators:
            result = v(t)
            if result.is_left:
                errors.update(result.value)

        if errors:
            return either.left(errors)

        return either.right(t)
