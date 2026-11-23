import unittest

from app.messages.normalizer import normalize_message
from app.messages.parser import ParsedMessage, parse_chat_line


class MessageParserTests(unittest.TestCase):
    def test_splits_player_and_message(self):
        self.assertEqual(
            parse_chat_line("Player123: jangan pergi mid dulu"),
            ParsedMessage("Player123", "jangan pergi mid dulu"),
        )

    def test_splits_allies_and_full_width_colon(self):
        self.assertEqual(
            parse_chat_line("[Allies] Fake Player： tunggu"),
            ParsedMessage("Fake Player", "tunggu"),
        )

    def test_localized_team_tags_keep_clan_brackets_in_the_name(self):
        for tag, speaker in (("【队友】", "Dilyar【UH.A】"), ("[队友]", "Dilyar[UH.A]")):
            with self.subTest(tag=tag):
                self.assertEqual(
                    parse_chat_line(f"{tag}{speaker}: อย่าไปคนเดียว"),
                    ParsedMessage(speaker, "อย่าไปคนเดียว"),
                )

    def test_uncertain_line_is_kept_whole(self):
        self.assertEqual(parse_chat_line("jangan pergi mid"), ParsedMessage(None, "jangan pergi mid"))

    def test_normalization_handles_case_spaces_and_terminal_punctuation(self):
        self.assertEqual(normalize_message("  Jangan   MID！！ "), "jangan mid")


if __name__ == "__main__":
    unittest.main()
