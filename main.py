from services import iam_service
from utils import log

logger = log.get_logger('MAIN')

logger.info("Iniciando processamento")

iam_service.disable_old_access_keys(5)