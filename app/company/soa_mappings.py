# Mapping for Statement of Accounts pages

# Summary mapping for pages: master type and breakdown document name
SUMMARY_PAGE_MAP = {
    'deposits': ('BS', '預貯金'),
    'notes_receivable': ('BS', '受取手形'),
    'accounts_receivable': ('BS', '売掛金'),
    'temporary_payments': ('BS', '仮払金'),
    'loans_receivable': ('BS', '貸付金'),
    'inventories': ('BS', '棚卸資産'),
    'securities': ('BS', '有価証券'),
    'fixed_assets': ('BS', '固定資産（土地等）'),
    'notes_payable': ('BS', '支払手形'),
    'accounts_payable': ('BS', '買掛金'),
    'temporary_receipts': ('BS', '仮受金'),
    'borrowings': ('BS', '借入金'),
    # PL-based pages
    'executive_compensations': ('PL', '役員給与等'),
    'land_rents': ('PL', '地代家賃等'),
    'miscellaneous': ('PL', '雑益・雑損失等'),
}

# Specific account mappings for PL pages where master does not provide breakdown_document linkage
PL_PAGE_ACCOUNTS = {
    'executive_compensations': ['役員報酬', '役員賞与'],
    'land_rents': ['地代家賃', '賃借料'],
    'miscellaneous': ['雑収入', '雑損失'],
}

