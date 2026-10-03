import asyncio

from blend.blend_engine.search_router import SearchRouter


class SlowWorkingProvider:
    async def search(self, query, use_tor=False, language='all', pageno=1, **kwargs):
        await asyncio.sleep(4.6)
        return [{
            'url': 'https://example.com/result',
            'title': 'Slow but valid result',
            'content': 'This came back after the initial timeout window.'
        }]

    def normalize(self, result):
        return result


def test_fast_search_retries_when_first_provider_times_out(monkeypatch):
    router = SearchRouter()

    monkeypatch.setattr(
        router.provider_manager,
        'get_providers',
        lambda category, engines: [SlowWorkingProvider()],
    )
    monkeypatch.setattr(router.result_processor, 'deduplicate', lambda results: results)
    monkeypatch.setattr(router.ranking_engine, 'rank_results', lambda results, query: results)

    payload = asyncio.run(router.route('example query', category='web', mode='fast'))

    assert payload['number_of_results'] == 1
    assert payload['results'][0]['title'] == 'Slow but valid result'
