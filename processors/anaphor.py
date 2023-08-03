
import spacy
import spacy_experimental

import logging
logging.basicConfig(level=logging.INFO)

nlp = spacy.load("en_core_web_sm")
nlp_coref = spacy.load("en_coreference_web_trf")

nlp_coref.replace_listeners("transformer", "coref", ["model.tok2vec"])
nlp_coref.replace_listeners("transformer", "span_resolver", ["model.tok2vec"])

nlp.add_pipe("coref", source=nlp_coref)

class Anaphor:

    @staticmethod
    def resolve(text, chat_history):
        full_text = '\n'.join(
            map(
                lambda chat: chat['reply'], 
                filter(
                    lambda chat: chat['ai'] == False, 
                    chat_history
                )
            )
        )
        full_text += '\n' + text
        doc = nlp(full_text)

        words_to_replace = {}
        for _, value in doc.spans.items():
            text = text.replace(str(value[1]), str(value[0]))

        return text