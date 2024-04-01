import spacy
from spacy.tokens import Doc, Token, Span
from datetime import timedelta

# Define custom token extensions
Token.set_extension("start_time", default=None)
Token.set_extension("end_time", default=None)
Token.set_extension("probability", default=None)
Token.set_extension("split", default=False)

Span.set_extension("start_time", default=None)
Span.set_extension("end_time", default=None)

Doc.set_extension("timestamp_doc", default="")

class SpacyWhisper:
    """
    A class for integrating Whisper transcriptions with SpaCy's NLP capabilities.

    Attributes:
        nlp (spacy.Language): A SpaCy Language object used for tokenization and other NLP tasks.
        word_level (bool): A flag indicating whether to process data at the word level.

    Methods:
        word_level_doc(whisper_output): Process Whisper output at the word level and create a SpaCy Doc.
        create_doc(whisper_output): Create a SpaCy Doc based on the specified processing level.
    """

    def __init__(self, lang, model=None, word_level=True, segments_key="segments", words_key="words"):
        """
        Initialize the SpacyWhisper class.

        Args:
            lang (str): Language code for SpaCy model.
            model (str, optional): Custom SpaCy model to load. Defaults to None, which loads a blank model for the specified language.
            word_level (bool, optional): Flag to indicate word level processing. Defaults to True.
        """
        self.segments_key = segments_key
        self.words_key = words_key
        if model:
            self.nlp = spacy.load(model)
        else:
            self.nlp = spacy.blank(lang)
        self.word_level = word_level

    def entity_assigner(self, doc):
        for ent in doc.ents:
            ent._.start_time = doc[ent.start]._.start_time
            ent._.end_time = doc[ent.end]._.end_time
        return doc

    def sent_assigner(self, doc):
        for sent in doc.sents:
            start = sent[0]._.start_time
            end = sent[-1]._.end_time

            sent._.start_time = start
            sent._.end_time = end

        return doc
    

    def doc_timestamp(self, doc):
        timestamp_doc = ""

        for sent in doc.sents:
            time = sent._.start_time

            # Check if time is None and assign a default value
            if time is None:
                time = 0.0

            # Convert time to a timedelta object
            time_delta = timedelta(seconds=float(time))

            # Format the time string
            hours, remainder = divmod(time_delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            milliseconds = int(time_delta.microseconds / 1000)

            timestamp = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
            timestamp_doc += f"[{timestamp}] {sent.text}\n"

        doc._.timestamp_doc = timestamp_doc
        return doc

    def word_level_doc(self, whisper_output):
        """
        Process Whisper output at the word level and create a SpaCy Doc.

        Args:
            whisper_output (dict): The output from Whisper containing segments and word information.

        Returns:
            spacy.tokens.Doc: The processed SpaCy Doc object.
        """
        # Join words from each segment to form the full text
        full_text = ' '.join(entry['word'].strip() for segment in whisper_output[self.segments_key] for entry in segment[self.words_key])

        # Tokenize the text using SpaCy
        doc = self.nlp(full_text)

        # Process each segment and set custom attributes for each token
        whisper_pointer = 0
        for segment in whisper_output[self.segments_key]:
            for entry in segment[self.words_key]:
                entry_word = entry['word'].strip()

                while whisper_pointer < len(doc):
                    token = doc[whisper_pointer]
                    token_text = token.text

                    if token_text in entry_word:
                        # Set token attributes
                        token._.start_time = entry['start']
                        token._.end_time = entry['end']
                        token._.probability = entry['probability']

                        # Check for punctuation and split tokens
                        if token_text != entry_word:
                            token._.split = True
                            if entry_word.endswith(token_text):
                                entry_word = ''  # Reset the entry word
                                whisper_pointer += 1
                                break
                        else:
                            entry_word = ''  # Reset the entry word
                            whisper_pointer += 1
                            break

                    whisper_pointer += 1
        doc = self.sent_assigner(doc)
        doc = self.doc_timestamp(doc)
        doc = self.entity_assigner(doc)
        return doc
    
    def process_whisper_output_word_level(self, whisper_output):
        """
        Process Whisper output at the word level, where each word in a segment has the same start and end time,
        and create a SpaCy Doc.

        Args:
            whisper_output (dict): The output from Whisper containing segments and word information.

        Returns:
            spacy.tokens.Doc: The processed SpaCy Doc object.
        """
        # Join words from each segment to form the full text
        full_text = ' '.join(segment['text'] for segment in whisper_output['segments'])

        # Tokenize the text using SpaCy
        doc = self.nlp(full_text)

        # Process each segment and set custom attributes for each token
        whisper_pointer = 0
        for segment in whisper_output['segments']:
            segment_start = segment.get('start', 0.0)  # Default to 0.0 if not available
            segment_end = segment.get('end', 0.0)  # Default to 0.0 if not available
            segment_text = segment['text'].strip()

            while whisper_pointer < len(doc):
                token = doc[whisper_pointer]
                token_text = token.text

                if token_text in segment_text:
                    # Set token attributes for the segment
                    token._.start_time = segment_start
                    token._.end_time = segment_end

                    # Check for punctuation and split tokens
                    if token_text != segment_text:
                        token._.split = True
                        if segment_text.endswith(token_text):
                            segment_text = ''  # Reset the segment text
                            whisper_pointer += 1
                            break
                    else:
                        segment_text = ''  # Reset the segment text
                        whisper_pointer += 1
                        break

                whisper_pointer += 1

        # Additional processing (if any)
        doc = self.sent_assigner(doc)
        doc = self.doc_timestamp(doc)
        doc = self.entity_assigner(doc)

        return doc



    def create_doc(self, whisper_output):
        """
        Create a SpaCy Doc based on the specified processing level.

        Args:
            whisper_output (dict): The output from Whisper containing segments and word information.

        Returns:
            spacy.tokens.Doc: The processed SpaCy Doc object.
        """
        if self.word_level:
            return self.word_level_doc(whisper_output)
        else:
            return self.process_whisper_output_word_level(whisper_output)
