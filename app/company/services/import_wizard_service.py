from __future__ import annotations

from collections.abc import Iterable


class UploadWizardService:
    """Session-backed helper for managing the upload wizard flow."""

    def __init__(self, flask_session, file_upload_steps: Iterable[str]):
        self.session = flask_session
        self.file_upload_steps = list(file_upload_steps)

    def selected_software(self) -> str | None:
        return self.session.get('selected_software')

    def has_selected_software(self) -> bool:
        return bool(self.selected_software())

    def completed_steps(self) -> list[str]:
        return list(self.session.get('wizard_completed_steps', []))

    def ensure_previous_steps_completed(self, datatype: str) -> str | None:
        if datatype not in self.file_upload_steps:
            return None
        completed = set(self.completed_steps())
        index = self.file_upload_steps.index(datatype)
        for step in self.file_upload_steps[:index]:
            if step not in completed:
                return step
        return None

    def next_pending_step(self) -> str | None:
        completed = set(self.completed_steps())
        for step in self.file_upload_steps:
            if step not in completed:
                return step
        return None

    def reset(self) -> None:
        self.session.pop('wizard_completed_steps', None)
        self.session.pop('selected_software', None)

    def store_unmatched_accounts(self, accounts) -> None:
        self.session['unmatched_accounts'] = accounts

    def clear_unmatched_accounts(self) -> None:
        self.session.pop('unmatched_accounts', None)
