from tests.with_dip.conftest import FakePriorityDetector
from with_dip.core import Priority
from with_dip.impl import RegexPriorityDetector


async def test_regex_priority_detector_returns_critical_without_calling_inner(
    priority_detector: FakePriorityDetector,
) -> None:
    # Arrange
    regex_priority_detector = RegexPriorityDetector(priority_detector)
    # Act
    priority = await regex_priority_detector.detect(
        "Production is down for all customers."
    )
    # Assert
    assert priority is Priority.CRITICAL
    assert priority_detector.detected_texts == []


async def test_regex_priority_detector_falls_back_to_inner_if_no_match(
    priority_detector: FakePriorityDetector,
) -> None:
    # Arrange
    regex_priority_detector = RegexPriorityDetector(priority_detector)
    # Act
    priority = await regex_priority_detector.detect(
        "The export button is slightly misaligned."
    )
    # Assert
    assert priority is Priority.NORMAL
    assert priority_detector.detected_texts == [
        "The export button is slightly misaligned."
    ]
