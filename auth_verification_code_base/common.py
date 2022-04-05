# Copyright 2022 Akretion
# Copyright 2022 Toodigit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

DEFAULT_VERIF_CODE_EXPIRY = 3600
DEFAULT_MAX_VERIF_CODE_ATTEMPTS = 5
DEFAULT_MAX_VERIF_CODE_DELAY = 5
DEFAULT_MAX_VERIF_CODE_GEN_DELAY = 15
DEFAULT_MAX_VERIF_CODE_GENERATION = 5


class TooManyVerifResendExc(Exception):
    pass
