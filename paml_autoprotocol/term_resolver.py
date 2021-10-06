import validators
from paml_autoprotocol.transcriptic_api import TranscripticAPI


class TermResolver():
    pass

class StrateosResolver(TermResolver):
    def __init__(self, api : TranscripticAPI = None):
        self.api = api
        self.connection = api.get_transcriptic_connection()

    def _is_uri(self, term: str):
        return validators.url(term)

    def resolve(self, term : str):
        try:
            if self._is_uri(term):
                resolved_term = self.lookup_uri(term)
            else:
                resolved_term = term

            results = self.connection.resources(resolved_term)["results"]
            print(f"Results for {term} ({resolved_term}): {results}")

        except ValueError as e:
            raise ValueError(f"Could not resolve term: {term}")

        assert(len(results) == 1)

        result = results[0]
        resource_id = result['id']
        return resource_id