import logging

from watcher.extension import db
from watcher.models import Alert

logger = logging.getLogger(__name__)

def evaluate_alerts(ignore_missing=False):
    """
    Harvest path stats and do alerts for conditions.
    """
    active_alerts = db.select(Alert).where(Alert.active)
    for alert in db.session.scalars(active_alerts):
        need_alerts = alert.alerts_for_paths(ignore_missing=ignore_missing)
        if not need_alerts:
            logger.info(f'no alerts for %s', alert.name)
        for alert, path_object in need_alerts:
            logger.info('Alert "%s" for %s', alert.name, path_object.path)
            alert.do_alert(path_object)
            db.session.commit()
