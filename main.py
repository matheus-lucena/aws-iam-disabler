from services import iam_service
from utils import log
from utils.env import DISABLE_ACCESS_KEY_DAYS


logger = log.get_logger('MAIN')
iam_service.disable_old_access_keys(DISABLE_ACCESS_KEY_DAYS)
