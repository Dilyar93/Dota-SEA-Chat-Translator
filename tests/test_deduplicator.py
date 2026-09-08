import unittest

from app.messages.deduplicator import MessageDeduplicator
from app.messages.parser import parse_chat_line


class DeduplicatorTests(unittest.TestCase):
    def test_required_frame_sequence_emits_only_new_messages(self):
        frames = {
            0: ["A: jangan mid"],
            1: ["A: jangan mid"],
            2: ["A: jangan mid"],
            3: ["A: jangan mid", "B: tunggu"],
            4: ["A: jangan mid", "B: tunggu"],
        }
        dedupe = MessageDeduplicator()
        events = []
        for second, lines in frames.items():
            for line in lines:
                message = parse_chat_line(line).message
                if dedupe.is_new(message, second):
                    events.append((second, message))
        self.assertEqual(events, [(0, "jangan mid"), (3, "tunggu")])

    def test_required_ocr_variants_are_fuzzy_duplicates(self):
        dedupe = MessageDeduplicator()
        self.assertTrue(dedupe.is_new("jangan pergi mid dulu", 0))
        self.assertFalse(dedupe.is_new("jangan pergl mid dulu", 1))
        self.assertFalse(dedupe.is_new("jangan pergi mid dulu.", 2))

    def test_message_can_reappear_after_window(self):
        dedupe = MessageDeduplicator(window_seconds=15)
        self.assertTrue(dedupe.is_new("tunggu", 0))
        self.assertTrue(dedupe.is_new("tunggu", 16))


if __name__ == "__main__":
    unittest.main()
