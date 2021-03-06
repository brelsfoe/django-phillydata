import logging

import reversion

from ..li.adapter import get_location
from .models import Violation, ViolationType
from .api import LIViolationReader


logger = logging.getLogger(__name__)


def find_violations(code, since, until=None):
    reader = LIViolationReader()
    for violation in reader.get(code, since=since, until=until):
        try:
            saved_violation = save_violation(violation)
            logger.debug('Added violation: %s' % saved_violation)
        except Exception:
            logger.exception('Failed to load violation: %s' % violation)


def find_violations_fill_case_number(code, since, until=None):
    """
    Get case_number from the API for violations that we likely already have.
    """
    reader = LIViolationReader()
    for violation in reader.get(code, since=since, until=until):
        try:
            existing_violation = Violation.objects.get(
                external_id=violation['violation_details_id']
            )
            existing_violation.case_number = violation['case_number']
            existing_violation.save()
            logger.debug('Updated violation: %s' % existing_violation)
        except Exception:
            try:
                saved_violation = save_violation(violation)
                logger.debug('Added violation: %s' % saved_violation)
            except Exception:
                logger.exception('Failed to load violation: %s' % violation)


def get_violation_type(violation):
    violation_type, created = ViolationType.objects.get_or_create(
        code=violation['violation_code'],
        li_description=violation['violation_code_description'],
    )
    return violation_type


@reversion.create_revision()
def save_violation(violation):
    location = get_location(violation)
    violation_type = get_violation_type(violation)

    saved_violation, created = Violation.objects.get_or_create(
        external_id=violation['violation_details_id'],
        case_number=violation['case_number'],
        violation_datetime=LIViolationReader.parse_datetime(violation.get('violation_datetime', None)),
        location=location,
        violation_type=violation_type,
    )

    return saved_violation
