"""Form re-exports grouped by domain to keep import paths stable."""
from __future__ import annotations

from .beppyo15 import Beppyo15BreakdownForm  # noqa: F401
from .declaration import (  # noqa: F401
    AccountingSelectionForm,
    CompanyForm,
    DataMappingForm,
    DeclarationForm,
    FileUploadForm,
    LoginForm,
    OfficeForm,
    SoftwareSelectionForm,
)
from .shareholders import (  # noqa: F401
    BaseShareholderForm,
    MainShareholderForm,
    RelatedShareholderForm,
)

# SoA forms are exposed via the new domain package; wildcard export keeps dynamic
# form classes (AccountsReceivableForm など) available under the legacy paths.
from .soa import *  # noqa: F401,F403
from .soa import (  # noqa: F401
    DepositForm,
    NotesPayableForm,
    NotesReceivableForm,
)
