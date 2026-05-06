from agentia.llm import LLMProvider


def test_llm_provider_protocol_is_runtime_checkable():
    class FakeProvider:
        def invoke(self, messages):
            ...

        async def astream(self, messages):
            yield

    assert isinstance(FakeProvider(), LLMProvider)


def test_class_missing_astream_does_not_satisfy_protocol():
    class Incomplete:
        def invoke(self, messages):
            ...

    assert not isinstance(Incomplete(), LLMProvider)
